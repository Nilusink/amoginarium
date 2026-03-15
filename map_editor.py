"""
map_editor.py
15.03.2026

edit maps

Author:
Nilusink
"""
from icecream import ic
import pygame as pg

from amoginarium.base import BaseGame, Updated
from amoginarium.ui import EventHandler, UIElement
from amoginarium.shared import global_vars
from amoginarium.logic import convert_coord, Vec2


def main() -> None:
    base = BaseGame(debug=True)
    base.load_map("assets/maps/tutorial.json")
    base.running = False

    mouse_down_pos = None
    last_mouse_pos = None

    def handle_zoom(event):
        global_vars.pixel_per_meter *= 1 + event.y / 30

    def handle_mouse_down(event):
        nonlocal mouse_down_pos
        mouse_down_pos = convert_coord(event.pos, Vec2)

    def handle_mouse_up(event):
        nonlocal mouse_down_pos, last_mouse_pos
        last_mouse_pos = None

        # if not mouse_down_pos:
        #     return
        #
        # delta = convert_coord(event.pos, Vec2), mouse_down_pos

    def handle_mouse(event):
        nonlocal last_mouse_pos
        if pg.mouse.get_pressed()[0]:
            now_pos = convert_coord(event.pos, Vec2)
            if last_mouse_pos:
                delta: Vec2 = last_mouse_pos - now_pos
                delta *= .5

                Updated.world_position += delta
                global_vars.world_position = Updated.world_position.copy()
                last_mouse_pos = now_pos

                base._background.set_position(global_vars.world_position.x)
                # base._background.scroll(.1)

            else:
                last_mouse_pos = now_pos

    EventHandler.add_event(pg.QUIT, callback=lambda e: base.end())
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
