"""
test for the map generator.

test_map_generator.py
15.05.2026

Author:
Nilusink
"""

from __future__ import annotations

import random
import typing as tp
from enum import Enum
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import pygame as pg
from icecream import ic
from scipy import ndimage

from amoginarium import pv
from amoginarium.base import BaseGame
from amoginarium.graphics.render_bindings import renderer
from amoginarium.logic.map import array_get, generate_chunk_noise, iterate_chunk, to_str
from amoginarium.shared.utility import Color, Vec2

if tp.TYPE_CHECKING:
    from numpy.typing import NDArray

DEBUG: tp.Final[bool] = False
ISLAND_SIZE: tp.Final[int] = 64
CHUNK_SIZE: tp.Final[int] = ISLAND_SIZE * 96
CHUNK_SMOOTHING_ITERATIONS: tp.Final[int] = 16
UPDATE_INTERVAL: tp.Final[float] = 0.0
MAX_LEN: tp.Final[int] = 8

PATH_DIR_WEIGHTS: list[int] = [
    6,
    2,
    1,
    1,
]

# spawn stuff
IDEAL_PLATEAU_LENGTH: tp.Final[int] = 8

# syntax: (name, required_space), spawn_weight, cluster_variant_chance
spawnables: tp.Final[list[tuple[tuple[str, tuple[float, float]], int, float]]] = [
    (("turret.static.ak47", (23, 0)), 6, 0),
    (("turret.static.minigun", (128, 0)), 4, 0),
    (("turret.static.sniper", (128, 0)), 4, 0),
    (("turret.static.cram", (64, 0)), 1, 0),
    (("turret.static.sky_shield", (128, 0)), 1, 0),
    (("turret.static.flak", (186, 0)), 2, 0),
    (("turret.static.mortar", (ISLAND_SIZE * 2, ISLAND_SIZE * 10)), 7, 0.5),
]


class IslandType(Enum):
    """Island connection types."""

    connect_8 = 0
    connect_4 = 1


def render_chunk(pos: Vec2, chunk: np.ndarray) -> None:
    """
    Render a chunk.

    :param pos:
    :param chunk:
    """
    world_pos = pv.global_vars.get_world_position()

    chunk_size_x = len(chunk)
    chunk_size_y = len(chunk[0])

    for col in range(chunk_size_x):
        for row in range(chunk_size_y):
            renderer.draw_rect(
                Vec2().from_cartesian(
                    col * ISLAND_SIZE,
                    row * ISLAND_SIZE,
                )
                - world_pos
                + pos,
                (ISLAND_SIZE, ISLAND_SIZE),
                Color().from_1(*(chunk[col, row],) * 3, 1),
            )


def draw_chunk_interface(pos: Vec2, if_type: int) -> None:
    """
    Draw interface for chunk.

    :param pos:
    :param if_type:
    """
    center_pos_ = pos.copy()
    center_pos_ += CHUNK_SIZE / 2
    pos_ = center_pos_.copy()
    if if_type == 0:
        pos_.x -= CHUNK_SIZE / 2

    elif if_type == 1:
        pos_.x += CHUNK_SIZE / 2

    elif if_type == 2:
        pos_.y -= CHUNK_SIZE / 2

    else:
        pos_.y += CHUNK_SIZE / 2

    renderer.draw_thick_line(
        center_pos_, pos_, Color().from_1(1, 1, 0), thickness=CHUNK_SIZE / 10
    )


def get_islands(
    source: NDArray[np.bool_],
    connection_type: IslandType = IslandType.connect_4,
) -> tuple[NDArray[np.int32], int]:
    """
    Get all islands from source chunk.

    :param source:
    :param connection_type:
    :return:
    """
    if connection_type == IslandType.connect_4:
        structure = np.array(
            [
                [0, 1, 0],
                [1, 1, 1],
                [0, 1, 0],
            ]
        )

    else:
        structure = np.ones((3, 3))

    # get standalone "islands"
    labels, num_islands = ndimage.label(source, structure=structure)

    return labels, num_islands  # type: ignore[rtype-OK]


def merge_chunks(
    chunks: dict[tuple[int, int], NDArray[np.float64]],
    masks: dict[tuple[int, int], NDArray[np.bool_]],
) -> tuple[NDArray[np.float64], NDArray[np.bool_], tuple[int, int]]:
    """
    Merge all small chunks into one big one.

    :param chunks: Your chunk
    :param masks: What in the holy mask
    :returns: merged ndarray, mask, min position
    """
    xs = [k[0] for k in chunks]
    ys = [k[1] for k in chunks]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    grid_w = max_x - min_x + 1
    grid_h = max_y - min_y + 1

    # create output array
    h, w = next(iter(chunks.values())).shape

    big = np.ones((grid_h * h, grid_w * w), dtype=np.float64)
    mask = np.zeros((grid_h * h, grid_w * w), dtype=np.bool)

    # insert chunks
    for ((cx, cy), chunk), mask_ in zip(chunks.items(), masks.values(), strict=True):
        x = (cx - min_x) * w
        y = (cy - min_y) * h

        big[y : y + h, x : x + w] = chunk.T
        mask[y : y + h, x : x + w] = mask_.T

    return big, mask, (min_x, min_y)


def top_of_column(island: np.ndarray, x: int, y_start: int = 0) -> int | None:
    """
    Find top of island via column scan.

    :param island: The island
    :param x: The x
    :param y_start: The y start
    :return: IDK
    """
    col = island[y_start:, x]
    ys = np.where(col)[0]
    return ys.min() if ys.size > 0 else None


def get_spawn_points(  # noqa: PLR0914
    island: NDArray[np.bool_],
    spawn_point: tuple[int, int],
    world: NDArray[np.float64],
    world_mask: NDArray[np.bool_],
) -> list[tuple[tuple[float, float], list[int]]]:
    """
    Get spawn point on island.

    :param island: The island
    :param spawn_point: The spawn point
    :param world: The world
    :param world_mask: The world mask
    :return: IDK
    :raises ValueError: IDK
    """
    island_height: int = len(island)

    # calculate plateaus
    # get surfaces
    labels, _ = get_islands(~island)
    target = labels[spawn_point[::-1]]

    if target == 0:
        msg = "Not inside a cave"
        raise ValueError(msg)

    # get caves
    cave_mask = labels == target
    cave = island.copy()
    cave[~cave_mask] = True  # outside = solid

    # extract surfaces
    surface = np.zeros_like(cave, dtype=bool)
    surface[1:, :] = cave[1:, :] & ~cave[:-1, :]
    surface &= cave

    # list of height, x_start, count  (list because settable)
    plateaus: list[tuple[int, int, int]] = []
    height, width = surface.shape
    for y in range(height):
        row = surface[y]

        x = 0
        while x < width:
            if not row[x]:
                x += 1
                continue

            start = x

            while x < width and row[x]:
                x += 1

            length = x - start

            plateaus.append((y, start, length))

    # create weights for plateaus (height + length)
    weights: list[float] = [
        (
            (
                (1 - (p[0] / island_height)) ** 2
                + min(1, p[2] / IDEAL_PLATEAU_LENGTH) ** 2 * 6
            )
            / 7
        )
        ** 2
        for p in plateaus
    ]

    out = []
    for plateau, weight in zip(plateaus, weights, strict=True):
        # check if point is out of bounds
        pos = (plateau[1] + plateau[2] // 2, plateau[0])
        world_pos = (
            pos[1] - 1,
            pos[0],
        )

        if not array_get(
            world_mask,
            world_pos,
            False,  # noqa: FBT003
        ):
            try:
                world[world_pos] = 1.5

            except IndexError:
                continue

            continue

        world[world_pos] = 2
        if random.random() < weight:
            world[world_pos] = 4
            out.append((pos, plateau))

    return out


def choose_turret(
    map_buffer: np.ndarray, spawn_pos: tuple[int, int], plateau: list[int]
) -> tuple[str, tuple[float, float], dict] | None:
    """
    Choose a turret based on map location.

    :param map_buffer: The map
    :return: IDK
    """
    turrets = []

    for turret in spawnables:
        x_size = turret[0][1][0] / ISLAND_SIZE
        y_size: int = 1 + int(turret[0][1][1] // ISLAND_SIZE)

        if x_size <= plateau[2]:
            # check height requirement
            headroom = top_of_column(map_buffer, spawn_pos[0], spawn_pos[1] - y_size)
            headroom = headroom or y_size

            if headroom < y_size - 1:
                ic("height fail", y_size, turret[0][1][1], headroom)
                # add visual hint to map buffer if height fail
                map_buffer[
                    spawn_pos[1] - y_size : max(1, spawn_pos[1] - y_size + headroom),
                    spawn_pos[0],
                ] = -2
                continue

            turret_args = {}

            if turret[2] > 0 and random.random() <= turret[2]:
                turret_args["cluster"] = True

            turrets.append(((*turret[0], turret_args), turret[1]))

        else:
            ic("size fail")

    if len(turrets) == 0:
        ic("no valid turrets found")
        return None

    names, counts = zip(*turrets, strict=True)
    return random.sample(names, 1, counts=counts)[0]


# noinspection DuplicatedCode
def main() -> None:  # noqa: C901, PLR0912, PLR0914, PLR0915
    """Da main func."""
    b = BaseGame(debug=True)
    renderer.display_set_windowed()

    screen_size = pv.global_vars.get_screen_size()
    screen_pixels = screen_size / pv.global_vars.get_pixel_per_meter()

    noise_scale = CHUNK_SIZE // ISLAND_SIZE

    running = True
    world_pos = Vec2()
    while True:
        i = 0
        last_update = perf_counter()
        current_chunk = (Vec2(), [])
        chunks: dict[tuple[int, int], tuple[Vec2, list[int]]] = {(0, 0): current_chunk}
        chunk_populations: dict[tuple[int, int], NDArray[np.float64]] = {}
        spawn_masks: dict[tuple[int, int], NDArray[np.bool_]] = {}

        while running:
            # handle pg events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                    break

            if not running:
                break

            # update chunks
            if perf_counter() - last_update > UPDATE_INTERVAL:
                # create new chunk
                old_pos_, *_ = current_chunk
                old_pos: tuple[int, int] = int(old_pos_.x), int(old_pos_.y)

                # create new direction
                viable_offsets = [
                    (int(old_pos[0]) + 1, int(old_pos[1])),
                    (int(old_pos[0]) - 1, int(old_pos[1])),
                    (int(old_pos[0]), int(old_pos[1]) + 1),
                    (int(old_pos[0]), int(old_pos[1]) - 1),
                ]
                new_positions = []
                weights = []
                for offset, weight in zip(
                    viable_offsets, PATH_DIR_WEIGHTS, strict=True
                ):
                    if not chunks.get(offset):
                        new_positions.append(offset)
                        weights.append(weight)

                if not new_positions:
                    # try to back-track
                    i -= 1
                    current_chunk = chunks[list(chunks.keys())[i]]

                else:
                    new_position = random.sample(new_positions, 1, counts=weights)[0]
                    new_pos = Vec2().from_cartesian(*new_position)
                    index = int(new_pos.x), int(new_pos.y)

                    direction_type = viable_offsets.index(new_position)

                    # set output pos of last chunk
                    old_chunk = chunks[old_pos]
                    chunk_directions = old_chunk[1]
                    chunk_directions.append(direction_type ^ 1)
                    chunks[old_pos] = (old_chunk[0], chunk_directions)  # type: ignore  # noqa: PGH003

                    current_chunk = (new_pos, [direction_type])
                    chunks[index] = current_chunk

                    last_update = perf_counter()
                    i = len(chunks) - 1

            if i < MAX_LEN and i % 10 != 1:
                continue

            # clear display
            renderer.clear_display()

            min_x = 0
            min_y = 0
            max_x = 0
            max_y = 0
            line = []
            for chunk in chunks.values():
                pos_, *_ = chunk
                pos_: Vec2
                pos = pos_.copy() * CHUNK_SIZE

                if chunk == current_chunk:
                    color = Color().from_1(1, 0, 0, 1)

                else:
                    color = Color().from_1(1, 1, 1, 1)

                renderer.draw_rect(pos - world_pos, (CHUNK_SIZE,) * 2, color)

                for direction in chunk[1]:
                    draw_chunk_interface(pos - world_pos, direction)

                if pos.x < min_x:
                    min_x = pos.x

                elif pos.x + CHUNK_SIZE > max_x:
                    max_x = pos.x + CHUNK_SIZE

                if pos.y < min_y:
                    min_y = pos.y

                elif pos.y + CHUNK_SIZE > max_y:
                    max_y = pos.y + CHUNK_SIZE

            renderer.draw_lines(
                line, Color().from_1(0.5, 0.5, 0.5, 1), thickness=CHUNK_SIZE / 3
            )

            # set view to center
            center_x = min_x + (max_x - min_x) / 2
            center_y = min_y + (max_y - min_y) / 2

            world_pos.xy = center_x, center_y
            world_pos -= screen_pixels / 2
            pv.global_vars.set_world_position(world_pos)

            # set zoom
            diff_x = max(1, max_x - min_x)
            diff_y = max(1, max_y - min_y)
            ppm_x = screen_size.x / diff_x
            ppm_y = screen_size.y / diff_y

            pv.global_vars.set_pixel_per_meter(min(ppm_x, ppm_y) * 0.7)
            screen_pixels = screen_size / pv.global_vars.get_pixel_per_meter()

            # flip display
            renderer.display_draw_frame()

            if i >= MAX_LEN:
                break

        if not running:
            ic(i)
            break

        renderer.clear_display()
        renderer.display_draw_frame()

        # generate chunks
        i = 0
        chunk_positions = list(chunks.keys())
        currently_populating = 0
        running = True
        while running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                    break

            # iterate chunks
            if currently_populating < len(chunks):
                curr_pos = chunk_positions[currently_populating]

                # generate chunk if it doesn't exist yet
                if i == 0:
                    chunk_populations[curr_pos], spawn_masks[curr_pos] = (
                        generate_chunk_noise(
                            (noise_scale,) * 2,
                            interfaces=chunks[curr_pos][1],
                            spawn_chunk=currently_populating == 0,
                        )
                    )

                if iterate_chunk(
                    chunk_populations[curr_pos], i, n_steps=CHUNK_SMOOTHING_ITERATIONS
                ):
                    i = 0
                    currently_populating += 1

                else:
                    i += 1

            else:
                running = False

            if i > 0:
                continue

            renderer.clear_display((0.8, 0.8, 0.8))

            for chunk in chunks.values():
                pos_, *_ = chunk
                pos_: Vec2
                pos = pos_.copy() * CHUNK_SIZE

                if chunk == current_chunk:
                    color = Color().from_1(1, 0, 0, 1)

                else:
                    color = Color().from_1(1, 1, 1, 1)

                renderer.draw_rect(pos - world_pos, (CHUNK_SIZE,) * 2, color)

                for direction in chunk[1]:
                    draw_chunk_interface(pos - world_pos, direction)

            for chunk_pos, chunk in chunk_populations.items():
                pos = Vec2().from_cartesian(*chunk_pos) * CHUNK_SIZE

                render_chunk(pos, chunk)

            renderer.display_draw_frame()

        # merge chunks
        big_chunk, chunk_mask, min_pos = merge_chunks(chunk_populations, spawn_masks)
        for _ in range(12):
            iterate_chunk(big_chunk, 0, 1)

        iterate_chunk(big_chunk, 2, 1)

        # group islands
        mask = big_chunk < 0.5
        structure = np.array(  # use 4-connected islands (no diagonals allowed)
            [
                [0, 1, 0],
                [1, 1, 1],
                [0, 1, 0],
            ]
        )
        labels, num_islands = ndimage.label(mask, structure=structure)

        islands: list[NDArray] = [  # type: ignore[trust-me-bro]
            (labels == i) for i in range(1, num_islands + 1)
        ]
        coords_list = [np.argwhere(labels == i) for i in range(1, num_islands + 1)]

        # write map
        block_size = 24 * 3
        min_pos = Vec2().from_cartesian(*min_pos) * CHUNK_SIZE
        spawn_pos = (
            Vec2().from_cartesian(
                CHUNK_SIZE / 2,
                CHUNK_SIZE / 2,
            )
            - min_pos
        )
        ic(min_pos.xy)

        ic("generating map data ...")
        map_data: dict[str, tp.Any] = {
            "name": "generated map",
            "background": random.randint(1, 4),
            "spawn_pos": spawn_pos.xy,
            "platforms": [],
            "entities": [],
        }

        # create islands
        for island, pts in zip(islands, coords_list, strict=True):
            min_y, min_x = pts.min(axis=0)
            max_y, max_x = pts.max(axis=0)

            cropped = island[min_y : max_y + 1, min_x : max_x + 1]
            pos = tuple(map(float, (min_x * ISLAND_SIZE, min_y * ISLAND_SIZE)))

            chunk = {
                "args": {
                    "pos": pos,
                    "form": cropped.tolist(),
                }
            }
            map_data["platforms"].append(chunk)

        # generate turrets
        i_spawn_ = spawn_pos / ISLAND_SIZE
        i_spawn = int(i_spawn_.x), int(i_spawn_.y)
        ic(i_spawn)
        for (x_off, y_off), plateau in get_spawn_points(
            big_chunk == 0, i_spawn, big_chunk, chunk_mask
        ):
            turret_ = choose_turret(
                big_chunk,
                (int(x_off), int(y_off)),
                plateau,
            )

            if not turret_:
                continue

            turret, _, args = turret_

            map_data["entities"].append(
                {
                    "type": turret,
                    "pos": (
                        x_off * ISLAND_SIZE + ISLAND_SIZE / 2,
                        y_off * ISLAND_SIZE,
                    ),
                    "args": args,
                }
            )

        # create spawn-platform
        spawn_pos -= Vec2().from_cartesian(block_size, -32)
        map_data["platforms"].append(
            {
                "type": "island.brick.green",
                "args": {
                    "pos": spawn_pos.xy,
                    "size": (block_size * 3, block_size * 2),
                },
            }
        )

        ic("writing map ...")
        with open("generated_map.json", "w", encoding="utf-8") as f:
            f.write(to_str(map_data))

        plt.imshow(big_chunk)
        plt.show()

        ic("done")
        b.end()
        return

    b.end()


if __name__ == "__main__":
    main()
