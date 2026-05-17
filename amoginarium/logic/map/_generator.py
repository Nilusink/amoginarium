"""
Python functions for the map generator.

Path: amoginarium/logic/map/_generator.py
Project: amoginarium
Created: 18.05.2026
Authors: Nilusink
"""

import numpy as np

_RNG = np.random.default_rng()


def generate_chunk_noise(
    size: tuple[int, int],
    *,
    interfaces: list[int],
    slice_multiplier: float = 1.4,
    spawn_chunk: bool = False,
    x_stretch: int = 4,
) -> np.ndarray:
    """
    Generate chunk noise with interface positions.

    :param size: chunk size
    :param interfaces: interface directions
    :param slice_multiplier: multiplier for interface slices
    :param spawn_chunk: if set, center of chunk will always be cleared
    :param x_stretch: noise stretch in x-axis
    :return: white noise
    """
    small: np.ndarray = _RNG.random((size[0] // x_stretch, size[1]))
    chunk = np.repeat(small, x_stretch, axis=0)

    x_start = int(size[0] / 5)
    x_mid = size[0] // 2
    x_end = size[0] - x_start

    y_start = int(size[1] / 5)
    y_mid = size[1] // 2
    y_end = size[1] - y_start

    for interface in interfaces:
        if interface == 0:  # left
            chunk[0:x_mid, y_start:y_end] *= slice_multiplier

        elif interface == 1:  # right
            chunk[x_mid:-1, y_start:y_end] *= slice_multiplier

        elif interface == 2:  # top  # noqa: PLR2004
            chunk[x_start:x_end, 0:y_mid] *= slice_multiplier

        else:  # bottom
            chunk[x_start:x_end, y_mid:-1] *= slice_multiplier

    if spawn_chunk:
        chunk[x_mid - 5 : x_mid + 5, y_mid - 5 : y_mid + 5] = 1

    return chunk
