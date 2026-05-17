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

import numpy as np
import pygame as pg
from certifi import core
from icecream import ic
from scipy import ndimage

from amoginarium import pv
from amoginarium.base import BaseGame
from amoginarium.graphics.render_bindings import renderer
from amoginarium.logic.map import preprocess, to_str
from amoginarium.shared.utility import Color, Vec2
from test_map_chunk_generator import generate_chunk_noise, iterate_chunk, render_chunk

ISLAND_SIZE: int = 64
CHUNK_SIZE = ISLAND_SIZE * ISLAND_SIZE
UPDATE_INTERVAL = 0.0000005
MAX_LEN: int = 16


def draw_chunk_interface(pos: Vec2, if_type: int) -> None:
    """draw "interface" for chunk"""

    # if_type -= 1

    _center_pos = pos.copy()
    _center_pos += CHUNK_SIZE / 2
    _pos = _center_pos.copy()
    if if_type == 0:
        _pos.x -= CHUNK_SIZE / 2

    elif if_type == 1:
        _pos.x += CHUNK_SIZE / 2

    elif if_type == 2:
        _pos.y -= CHUNK_SIZE / 2

    else:
        _pos.y += CHUNK_SIZE / 2

    # renderer.draw_circle(_pos, CHUNK_SIZE / 10, 8, Color().from_1(1, 1, 0))
    renderer.draw_thick_line(
        _center_pos, _pos, Color().from_1(1, 1, 0), thickness=CHUNK_SIZE / 10
    )


def merge_chunks(
    chunks: dict[tuple[int, int], np.ndarray],
) -> tuple[np.ndarray, tuple[int, int]]:
    """
    merge all small chunks into one big one

    :returns: merged ndarray, min position
    """
    xs = [k[0] for k in chunks.keys()]
    ys = [k[1] for k in chunks.keys()]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    grid_w = max_x - min_x + 1
    grid_h = max_y - min_y + 1

    # create output array
    h, w = next(iter(chunks.values())).shape

    big = np.ones((grid_h * h, grid_w * w), dtype=np.float32)

    # insert chunks
    for (cx, cy), chunk in chunks.items():
        x = (cx - min_x) * w
        y = (cy - min_y) * h

        big[y : y + h, x : x + w] = np.rot90(chunk, -1)[:, ::-1]

    return big, (min_x, min_y)


def top_of_column(island: np.ndarray, x: int):
    """find top of island via column scan"""
    col = island[:, x]
    ys = np.where(col)[0]
    return ys.min() if ys.size > 0 else None


def choose_turret(
    map_buffer: np.ndarray, spawn_pos: tuple[int, int]
) -> tuple[str, tuple[float, float]]:
    """choose a turret based on map location"""
    turrets = [
        (("turret.static.ak47", (11.5, 0)), 5),
        (("turret.static.minigun", (11.5, 0)), 3),
        (("turret.static.sniper", (11.5, 0)), 3),
        (("turret.static.flak", (186 / 2, 0)), 1),
        (("turret.static.cram", (32, 0)), 1),
        (("turret.static.sky_shield", (64, 0)), 1),
    ]
    if 1:
        turrets.append((("turret.static.mortar", (11.5, 0)), 7))

    names, counts = zip(*turrets)
    return random.sample(names, 1, counts=counts)[0]


def main() -> None:
    """d"""
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
                old_pos = (int(_old_pos.x), int(_old_pos.y))

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
                for offset, weight in zip(viable_offsets, viable_weights):
                    if not chunks.get(offset, False):  # type: ignore
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
                    chunks[old_pos] = (old_chunk[0], chunk_directions)  # type: ignore

                    current_chunk = (new_pos, [direction_type])
                    chunks[index] = current_chunk

                    last_update = perf_counter()
                    i = len(chunks) - 1

            if i < MAX_LEN and not i % 10 == 1:
                continue

            # clear display
            renderer.clear_display()

            min_x = 0
            min_y = 0
            max_x = 0
            max_y = 0
            line = []
            for _i, chunk in enumerate(chunks.values()):
                _pos, *_ = chunk
                _pos: Vec2
                pos = _pos.copy() * CHUNK_SIZE
                # line.append(pos - world_pos + CHUNK_SIZE/2)

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
            # center = current_chunk[0].copy() * CHUNK_SIZE
            # center += CHUNK_SIZE / 2
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

                if iterate_chunk(chunk_populations[curr_pos], i):
                    i = 0
                    currently_populating += 1

                else:
                    i += 1

            else:
                running = False

            if i > 0:
                continue

            renderer.clear_display((0.8, 0.8, 0.8))

            for _i, chunk in enumerate(chunks.values()):
                _pos, *_ = chunk
                _pos: Vec2
                pos = _pos.copy() * CHUNK_SIZE
                # line.append(pos - world_pos + CHUNK_SIZE/2)

                if chunk == current_chunk:
                    color = Color().from_1(1, 0, 0, 1)

                else:
                    color = Color().from_1(1, 1, 1, 1)

                renderer.draw_rect(pos - world_pos, (CHUNK_SIZE,) * 2, color)

                for direction in chunk[1]:
                    draw_chunk_interface(pos - world_pos, direction)

            for chunk_pos in chunk_populations:
                pos = Vec2().from_cartesian(*chunk_pos) * CHUNK_SIZE

                render_chunk(pos, chunk_populations[chunk_pos])

            renderer.display_draw_frame()

        # merge chunks
        big_chunk, min_pos = merge_chunks(chunk_populations)
        for _ in range(12):
            iterate_chunk(big_chunk, 0)

        iterate_chunk(big_chunk, np.inf, show_chunk=True)

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
        for island, pts in zip(islands, coords_list):
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
            island_height = len(cropped)
            island_length = len(cropped[0])

            spawn_chance = island_length / (CHUNK_SIZE / ISLAND_SIZE)

            if random.random() <= spawn_chance:
                o_heights = [top_of_column(cropped, _i) for _i in range(island_length)]
                heights = [v for v in o_heights if v is not None]

                # the higher, the more likely the spawn
                weights = [
                    int(((1 - (value / island_height)) ** 2) * 255) for value in heights
                ]
                ic(heights, weights)

                chosen_height = random.sample(heights, 1, counts=weights)[0]
                chosen_x_offset = o_heights.index(chosen_height)

                turret, offset = choose_turret(
                    big_chunk, (min_x + chosen_x_offset, min_y + chosen_height)
                )

                ic(turret)

                map_data["entities"].append(
                    {
                        "type": turret,
                        "pos": (
                            pos[0] + chosen_x_offset * ISLAND_SIZE + offset[0],
                            pos[1] + chosen_height * ISLAND_SIZE + offset[1],
                        ),
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
        with open("generated_map.json", "w") as f:
            f.write(to_str(map_data))

        ic("done")
        b.end()
        return

        running = True
        while running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                    break

            renderer.clear_display()

            for _i, chunk in enumerate(chunks.values()):
                _pos, *_ = chunk
                _pos: Vec2
                pos = _pos.copy() * CHUNK_SIZE
                # line.append(pos - world_pos + CHUNK_SIZE/2)

                if chunk == current_chunk:
                    color = Color().from_1(1, 0, 0, 1)

                else:
                    color = Color().from_1(1, 1, 1, 1)

                renderer.draw_rect(pos - world_pos, (CHUNK_SIZE,) * 2, color)

                for direction in chunk[1]:
                    draw_chunk_interface(pos - world_pos, direction)

            for chunk_pos in chunk_populations:
                pos = Vec2().from_cartesian(*chunk_pos) * CHUNK_SIZE

                render_chunk(pos, chunk_populations[chunk_pos])

            renderer.display_draw_frame()

        if not running:
            ic(i)
            break

    b.end()


if __name__ == "__main__":
    main()
