"""
test_map_generator.py
15.05.2026

test for the map generator

Author:
Nilusink
"""

from time import perf_counter
from icecream import ic
import pygame as pg
import random
import time

from amoginarium.graphics.render_bindings import renderer
from amoginarium.shared.utility import Color, Vec2
from amoginarium.base import BaseGame
from amoginarium import pv


CHUNK_SIZE = 4096
UPDATE_INTERVAL = .0000005
MAX_LEN: int = 1_000


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
    renderer.draw_thick_line(_center_pos, _pos, Color().from_1(1, 1, 0), thickness=CHUNK_SIZE/10)


def main() -> None:
    """ d """
    b = BaseGame(debug=True)
    renderer.display_set_windowed()

    screen_size = pv.global_vars.get_screen_size()
    screen_pixels = (
        screen_size / pv.global_vars.get_pixel_per_meter()
    )

    running = True
    world_pos = Vec2()
    while True:
        i = 0
        last_update = perf_counter()
        current_chunk = (Vec2(), [])
        chunks: dict[tuple[int, int], tuple[Vec2, list[int]]] = {(0, 0): current_chunk}

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
                old_pos = int(_old_pos.x), int(_old_pos.y)
    
                # create new direction
                viable_weights = [
                    1,
                    1,
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
                    # ic(len(chunks))
                    # break

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

                renderer.draw_rect(
                    pos - world_pos,
                    (CHUNK_SIZE,)*2,
                    color
                )

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
                line,
                Color().from_1(.5, .5, .5, 1),
                thickness=CHUNK_SIZE/3
            )
    
            # set view to center
            # center_x = min_x + (max_x - min_x) / 2
            # center_y = min_y + (max_y - min_y) / 2
            center = current_chunk[0].copy() * CHUNK_SIZE
            center += CHUNK_SIZE / 2
            world_pos.xy = center.xy  # center_x, center_y
            world_pos -= screen_pixels / 2
            pv.global_vars.set_world_position(world_pos)
    
            # set zoom
            diff_x = max(1, max_x - min_x)
            diff_y = max(1, max_y - min_y)
            ppm_x = screen_size.x / diff_x
            ppm_y = screen_size.y / diff_y
    
            pv.global_vars.set_pixel_per_meter(min(ppm_x, ppm_y))
            screen_pixels = (
                screen_size / pv.global_vars.get_pixel_per_meter()
            )
    
            # flip display
            renderer.display_draw_frame()
    
            if i >= MAX_LEN:
                break

        if not running:
            ic(i)
            break

        time.sleep(5)

    b.end()


if __name__ == "__main__":
    main()
