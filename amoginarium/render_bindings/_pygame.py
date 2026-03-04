"""
_pygame.py
23. March 2024

a few functions for rendering

Author:
Nilusink
"""
# from pygame.locals import DOUBLEBUF, OPENGL
from icecream import ic
from PIL import Image
import pygame as pg
import numpy as np

from ..logic import Vec2, Color, convert_coord
from ._base_renderer import BaseRenderer
from ..shared import global_vars

# define types
type TextureID = pg.Surface


class PyGameRenderer(BaseRenderer):
    def init(self, title):
        ic("using pygame backend")

        pg.font.init()

        # get screen size
        screen_info = pg.display.Info()
        window_size = (screen_info.current_w, screen_info.current_h)

        # set global screen size and ppm
        global_vars.screen_size = Vec2.from_cartesian(*window_size)
        global_vars.screen_size_real = Vec2.from_cartesian(*window_size)
        global_vars.pixel_per_meter = window_size[0] / 1920
        global_vars.max_fps = max(pg.display.get_desktop_refresh_rates())

        self.screen = pg.display.set_mode(window_size, pg.RESIZABLE)
        # self.lowest_layer = pg.Surface(window_size, pg.SRCALPHA, 32)
        # self.middle_layer = pg.Surface(window_size, pg.SRCALPHA, 32)
        # self.top_layer = pg.Surface(window_size, pg.SRCALPHA, 32)
        self.font = pg.font.SysFont(None, 24)
        pg.display.set_caption(title)

    @staticmethod
    def load_texture(
            image,
            size,
            mirror=""
    ) -> tuple[TextureID, tuple[int, int]]:
        if size is not None:
            image = image.resize(convert_coord(size))

        if "x" not in mirror:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # Flip the image vertically (since OpenGL's origin is at bottom-left)
        if "y" in mirror:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

        width, height = image.size

        # convert image to pygame surface
        pygame_surface = pg.image.fromstring(
            image.tobytes(),
            image.size,
            "RGBA"
        )

        return pygame_surface, (width, height)

    def draw_textured_quad(
            self,
            texture_id: TextureID,
            pos,
            size,
            convert_global=True
    ):
        pos = convert_coord(pos, Vec2)
        size = convert_coord(size, Vec2)

        # convert to screen realtive coords and size
        if convert_global:
            pos = global_vars.translate_screen_coord(pos)
            size = global_vars.translate_scale(size)

        # resize image if necessary
        if texture_id.get_size() != size.xy:
            texture_id = pg.transform.scale(texture_id, size.xy)

        # draw image on screen
        self.screen.blit(texture_id, pos.xy)

    def draw_circle(
            self,
            center,
            radius,
            num_segments,
            color,
            convert_global=True
    ):
        center = convert_coord(center, Vec2)
        color = color if isinstance(color, Color) else Color.from_1(*color)

        # convert to screen realtive coords and size
        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        pg.draw.circle(
            self.screen,
            color.auto255,
            center.xy,
            radius
        )

    def draw_rect(
            self,
            start,
            size,
            color,
            convert_global=True
    ):
        start = convert_coord(start, Vec2)
        size = convert_coord(size, Vec2)
        color = color if isinstance(color, Color) else Color.from_1(*color)

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            size = global_vars.translate_scale(size)

        pg.draw.rect(
            self.screen,
            color.auto255,
            (start.xy, size.xy)
        )

    def draw_dashed_circle(
            self,
            center,
            radius,
            num_segments,
            color,
            thickness=1,
            convert_global=True
    ):
        center = convert_coord(center, Vec2)
        color = color if isinstance(color, Color) else Color.from_1(*color)

        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        for i in range(num_segments):
            i1 = i * 2
            i2 = i1 + 1

            cosine1 = np.cos(i1 * 2 * np.pi / num_segments)
            sine1 = np.sin(i1 * 2 * np.pi / num_segments)

            cosine2 = np.cos(i2 * 2 * np.pi / num_segments)
            sine2 = np.sin(i2 * 2 * np.pi / num_segments)

            p1 = cosine1 * radius, sine1 * radius
            p2 = (
                cosine1 * (radius + thickness),
                sine1 * (radius + thickness)
            )
            p3 = (
                cosine2 * (radius + thickness),
                sine2 * (radius + thickness)
            )
            p4 = cosine2 * radius, sine2 * radius

            pg.draw.polygon(
                self.screen,
                color.auto255,
                (p1, p2, p3, p4)
            )

    def draw_line(
            self,
            start,
            end,
            color,
            global_position=True,
            convert_global=True
    ):
        """
        draw a simple line
        """
        start = convert_coord(start, Vec2)
        end = convert_coord(end, Vec2)

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            end = global_vars.translate_scale(end)

        pg.draw.line(
            self.screen,
            color.auto255,
            start.xy,
            end.xy
        )
