"""
Global debug overlay.

| ``Path``: amoginarium/graphics/debug_menu.py
| ``Project``: amoginarium
| ``Created``: 28.05.2026
| ``Authors``: Nilusink
"""

import typing as tp

import pygame as pg

from amoginarium import pv
from amoginarium.shared import DebugVarsEnum

from .render_bindings import renderer

DEBUG_KEYBINDS: dict[int, tuple[str, DebugVarsEnum]] = {
    pg.K_F1: ("(F1) Hitboxes", DebugVarsEnum.DRAW_HITBOXES),
    pg.K_F2: ("(F2) Adv. Debugging", DebugVarsEnum.ADV_DEBUGGING),
}


def draw_debug_overlay(*, paused: bool, slo_mo: bool) -> None:
    """
    Draw debug overlay.

    :param paused: Is game paused?
    :param slo_mo: Is game in slo-mo?
    """
    screen_size = pv.global_vars.get_screen_size()
    padding = screen_size.x / 100
    font_size = screen_size.x / 128
    line_height = 1.3

    # draw top-left box
    renderer.draw_rounded_rect(
        (-10, -10),
        (
            screen_size.x / 6,
            font_size * line_height * (len(DEBUG_KEYBINDS) + 5),
        ),
        (0, 0, 0, 0.5),
        20,
        offscreen_check=False,
        convert_global=False,
    )

    # draw red outline
    renderer.draw_rect_line(
        (0, 0),
        screen_size,
        (1, 0, 0),
        thickness=5,
        convert_global=False,
    )

    # draw vars
    curr_y = padding

    # manually add paused + slo_mo because they aren't global debug variables
    debug_vars = [
        ("(Pause) Paused", paused),
        ("(Down) Slo-mo", slo_mo)
    ] + [
        (name, pv.global_vars.get_debug_var(debug_var))
        for name, debug_var in DEBUG_KEYBINDS.values()
    ]

    for name, value in debug_vars:
        # draw checkbox
        renderer.draw_circle(
            (padding + font_size / 2, curr_y + font_size / 1.6),
            font_size / 2,
            16,
            (0.2, 1, 0.2) if value else (1, 0.2, 0.2),
            convert_global=False,
            offscreen_check=False,
        )

        # draw text
        renderer.draw_dynamic_text(
            (2 * padding, curr_y),
            name,
            color=(1, 1, 1, 1),
            font_size=font_size,
            font_family="monospace",
            offscreen_check=False,
            convert_global=False,
        )
        curr_y += font_size * line_height
