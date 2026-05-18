"""
test for the map generator.

test_map_generator.py
15.05.2026

Author:
Nilusink
"""

import random
import typing as tp
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

ISLAND_SIZE: int = 64
CHUNK_SIZE = ISLAND_SIZE * 96
CHUNK_SMOOTHING_ITERATIONS: int = 16
UPDATE_INTERVAL = 0.0
MAX_LEN: int = 8

# spawn stuff
IDEAL_PLATEAU_LENGTH: int = 8

# syntax: (name, required_space), spawn_weight, cluster_variant_chance
spawnables: list[tuple[tuple[str, tuple[float, float]], int, float]] = [
    (("turret.static.ak47", (23, 0)), 6, 0),
    (("turret.static.minigun", (128, 0)), 4, 0),
    (("turret.static.sniper", (128, 0)), 4, 0),
    (("turret.static.cram", (64, 0)), 1, 0),
    (("turret.static.sky_shield", (128, 0)), 1, 0),
    (("turret.static.flak", (186, 0)), 2, 0),
    (("turret.static.mortar", (ISLAND_SIZE * 2, ISLAND_SIZE * 10)), 7, 0.5),
]


def render_chunk(pos: Vec2, chunk: np.ndarray) -> None:
    """Render a chunk."""
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
    """Draw interface for chunk."""
    _center_pos = pos.copy()
    _center_pos += CHUNK_SIZE / 2
    _pos = _center_pos.copy()
    if if_type == 0:
        _pos.x -= CHUNK_SIZE / 2

    elif if_type == 1:
        _pos.x += CHUNK_SIZE / 2

    elif if_type == 2:  # noqa: PLR2004
        _pos.y -= CHUNK_SIZE / 2

    else:
        _pos.y += CHUNK_SIZE / 2

    renderer.draw_thick_line(
        _center_pos, _pos, Color().from_1(1, 1, 0), thickness=CHUNK_SIZE / 10
    )


def merge_chunks(
    chunks: dict[tuple[int, int], np.ndarray],
) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    """
    Merge all small chunks into one big one.

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
    for (cx, cy), chunk in chunks.items():
        x = (cx - min_x) * w
        y = (cy - min_y) * h

        big[y : y + h, x : x + w] = chunk.T
        mask[y : y + h, x : x + w] = True

    return big, mask, (min_x, min_y)


def top_of_column(island: np.ndarray, x: int, y_start: int = 0) -> int | None:
    """Find top of island via column scan."""
    col = island[y_start:, x]
    ys = np.where(col)[0]
    return ys.min() if ys.size > 0 else None


def get_spawn_probability(_island: np.ndarray) -> float:
    """
    Get spawn probability of an island.
    """
    return 1


def get_spawn_points(
    island: np.ndarray,
    island_start: tuple[int, int],
    world: np.ndarray,
    world_mask: np.ndarray,
) -> list[tuple[tuple[float, float], list[int]]]:
    """Get spawn point on island."""
    island_height: int = len(island)
    island_length: int = len(island[0])

    # get top of island for each x position
    o_heights: list[int] = [
        island_height if (v := top_of_column(island, ind)) is None else v
        for ind in range(island_length)
    ]

    # calculate plateaus
    # list of height, x_start, count  (list because settable)
    plateaus: list[list[int]] = []
    current_plateau = -1
    for i in range(len(o_heights)):
        current_height = o_heights[i]

        if current_height != current_plateau:
            plateaus.append([int(current_height), i, 0])
            current_plateau = current_height

        # add step to plateau
        plateaus[-1][-1] += 1

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
            island_start[1] + pos[1] - 1,
            island_start[0] + pos[0],
        )

        if not array_get(
            world_mask,
            world_pos,
            False,
        ):
            try:
                world[world_pos] = 5

            except IndexError:
                continue

            continue

        if random.random() < weight:
            world[world_pos] = 10
            out.append((pos, plateau))

    return out


def choose_turret(
    map_buffer: np.ndarray, spawn_pos: tuple[int, int], plateau: list[int]
) -> tuple[str, tuple[float, float], dict] | None:
    """Choose a turret based on map location."""
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
        chunk_populations: dict[tuple[int, int], np.ndarray] = {}

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
                _old_pos, *_ = current_chunk
                old_pos: tuple[int, int] = int(_old_pos.x), int(_old_pos.y)

                # create new direction
                viable_weights = [
                    8,
                    3,
                    1,
                    1,
                ]
                viable_offsets = [
                    (int(old_pos[0]) + 1, int(old_pos[1])),
                    (int(old_pos[0]) - 1, int(old_pos[1])),
                    (int(old_pos[0]), int(old_pos[1]) + 1),
                    (int(old_pos[0]), int(old_pos[1]) - 1),
                ]
                new_positions = []
                weights = []
                for offset, weight in zip(viable_offsets, viable_weights, strict=True):
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
                    chunk_populations[curr_pos] = generate_chunk_noise(
                        (noise_scale,) * 2,
                        interfaces=chunks[curr_pos][1],
                        spawn_chunk=currently_populating == 0,
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
        big_chunk, chunk_mask, min_pos = merge_chunks(chunk_populations)
        for _ in range(12):
            iterate_chunk(big_chunk, 0, 1)

        iterate_chunk(big_chunk, 2, 1)

        # group islands
        mask = big_chunk < 0.5  # noqa: PLR2004
        structure = np.array(  # use 4-connected islands (no diagonals allowed)
            [
                [0, 1, 0],
                [1, 1, 1],
                [0, 1, 0],
            ]
        )
        labels, num_islands = ndimage.label(mask, structure=structure)

        islands = [(labels == i) for i in range(1, num_islands + 1)]
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

            # create turrets
            # get tops of island
            spawn_chance = get_spawn_probability(cropped)

            if random.random() <= spawn_chance:
                for (x_off, y_off), plateau in get_spawn_points(
                    cropped, (min_x, min_y), big_chunk, chunk_mask
                ):
                    # calculate global position
                    x_pos = min_x + x_off
                    y_pos = min_y + y_off

                    turret_ = choose_turret(big_chunk, (x_pos, y_pos), plateau)

                    if not turret_:
                        continue

                    turret, _, args = turret_

                    map_data["entities"].append(
                        {
                            "type": turret,
                            "pos": (
                                pos[0] + x_off * ISLAND_SIZE + ISLAND_SIZE / 2,
                                pos[1] + y_off * ISLAND_SIZE,
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
