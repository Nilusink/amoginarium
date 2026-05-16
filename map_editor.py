"""
map_editor.py
15.03.2026

edit maps

Author:
Nilusink
"""

from contextlib import suppress

import pygame as pg
from icecream import ic

from amoginarium.base import BaseGame
from amoginarium.graphics.ui import EventHandler
from amoginarium.logic.entities import CollisionDestroyed, Updated
from amoginarium.logic.map import save_map
from amoginarium.shared import GameEntityLike, VisibleGameEntityLike
from amoginarium.shared.utility import Vec2, convert_coord


def main() -> None:
    base = BaseGame(debug=True)
    base.load_map("test_map.json")
    # base.load_map("test_map.json")
    base.running = False

    # k = KeyboardController.get()
    # p = Player(Coalitions.blue, k)

    mouse_down_pos = None
    last_mouse_pos = None
    selected: GameEntityLike | None = None
    selected_offset: Vec2 | None = None

    def handle_quit(_event):
        save_map("test_map.json")
        base.end()

    def handle_zoom(event):
        global_vars.pixel_per_meter *= 1 + event.y / 30

    def handle_mouse_down(event):
        nonlocal mouse_down_pos
        mouse_down_pos = convert_coord(event.pos, Vec2)

        if selected:
            ic(selected)

    def handle_mouse_up(event):
        nonlocal mouse_down_pos, last_mouse_pos
        last_mouse_pos = None

    def handle_mouse(event):
        nonlocal last_mouse_pos, selected, selected_offset

        mouse_pos = event.pos
        x = convert_coord(
            (
                (mouse_pos[0] / global_vars.pixel_per_meter)
                * global_vars.screen_size_fac_x,
                (mouse_pos[1] / global_vars.pixel_per_meter)
                * global_vars.screen_size_fac_y,
            ),
            Vec2,
        )

        # moving
        if pg.mouse.get_pressed()[0]:
            # now_pos = convert_coord(events.pos, Vec2)
            if last_mouse_pos:
                delta: Vec2 = last_mouse_pos - x
                # delta *= (1 / global_vars.pixel_per_meter)

                # move entity
                if selected:
                    selected.position = x + Updated.world_position - selected_offset
                    selected.update_rect()

                # move world
                else:
                    Updated.world_position += delta
                    last_mouse_pos = x

                    base._background.set_position(global_vars.world_position.x)

            else:
                last_mouse_pos = x.copy()

        # entity highlight
        mouse_pos = x + Updated.world_position

        if any(
            [
                not selected,
                selected
                and not CollisionDestroyed.point_in_sprite(selected, mouse_pos.xy),
            ]
        ):
            for entity in Updated.entities():
                entity: VisibleGameEntityLike

                if hasattr(entity, "highlight"):
                    if CollisionDestroyed.point_in_sprite(entity, mouse_pos.xy):
                        if hasattr(entity, "mask"):
                            top_left = convert_coord(entity.rect.topleft, Vec2)
                            delta = mouse_pos - top_left

                            with suppress(IndexError):
                                if entity.mask.get_at(delta.xy):
                                    entity.highlight()
                                    selected = entity
                                    selected_offset = delta + (
                                        entity.position - top_left
                                    )
                                    break

                    entity.stop_highlight()

            else:
                selected = None

    EventHandler.add_event(pg.QUIT, callback=handle_quit)
    EventHandler.add_event(pg.MOUSEWHEEL, callback=handle_zoom)
    EventHandler.add_event(pg.MOUSEBUTTONDOWN, callback=handle_mouse_down)
    EventHandler.add_event(pg.MOUSEBUTTONUP, callback=handle_mouse_up)
    EventHandler.add_event(pg.MOUSEMOTION, callback=handle_mouse)

    Updated.world_position.y = -(
        (global_vars.screen_size.y / global_vars.pixel_per_meter)
        - global_vars.screen_size.y
    )
    global_vars.world_position.y = Updated.world_position.y
    while True:
        base.draw_entities_only()
        EventHandler.check_events()


if __name__ == "__main__":
    main()
