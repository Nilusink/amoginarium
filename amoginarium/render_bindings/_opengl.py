"""
_opengl.py
21. March 2024

a few functions for rendering

Author:
Nilusink
"""
from OpenGL.GL import glTranslate, glMatrixMode, glLoadIdentity, glTexCoord2f
from OpenGL.GL import glBindTexture, glTexParameteri, glTexImage2D, glEnable
from OpenGL.GL import glGenTextures, glVertex2f, glColor3f, glColor4f, glEnd
from OpenGL.GL import glDisable, glBegin, glVertex, glFlush, glClearColor
from OpenGL.GL import glBlendFunc, glWindowPos2d, glDrawPixels, glRotated
from OpenGL.GL import GL_UNSIGNED_BYTE, GL_MODELVIEW, GL_ONE_MINUS_SRC_ALPHA
from OpenGL.GL import GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT, GL_LINES
from OpenGL.GL import GL_TEXTURE_WRAP_T, GL_TEXTURE_MIN_FILTER, GL_POLYGON
from OpenGL.GL import GL_TEXTURE_MAG_FILTER, GL_LINEAR, GL_RGBA, GL_QUADS
from OpenGL.GL import GL_PROJECTION, GL_SRC_ALPHA, GL_BLEND
from OpenGL.GLU import gluOrtho2D
from pygame.locals import DOUBLEBUF, OPENGL
from icecream import ic
from PIL import Image
import pygame as pg
import numpy as np
import math as m

from ..logic import Vec2, Color, convert_coord
from ._base_renderer import BaseRenderer, tColor
from ..base._linked import global_vars


# define types
type TextureID = int


class OpenGLRenderer(BaseRenderer):
    def _get_font(
            self,
            size: int,
            family: str,
            bold: bool = False,
            italic: bool = False
    ) -> pg.font.Font:
        # check if font exists
        if size in self._fonts:
            for font in self._fonts[size]:
                if all([
                    font.name == family,
                    font.bold == bold,
                    font.italic == italic
                ]):
                    return font

        else:
            self._fonts[size] = []

        # no font found, create new
        new_font = pg.font.SysFont(family, size, bold, italic)
        self._fonts[size].append(new_font)

        return new_font

    def init(self, title):
        ic("using OpenGL backend")

        pg.font.init()

        self._fonts = {
            32: [
                pg.font.SysFont('arial', 32)
            ],
            64: [
                pg.font.SysFont('arial', 64)
            ]
        }

        # get screen size
        screen_info = pg.display.Info()
        window_size = (screen_info.current_w, screen_info.current_h)

        # set global screen size and ppm
        global_vars.screen_size = Vec2.from_cartesian(*window_size)
        global_vars.pixel_per_meter = window_size[0] / 1920

        # set max fps to monitor refresh rate
        global_vars.max_fps = max(pg.display.get_desktop_refresh_rates())

        pg.display.set_mode(
            global_vars.screen_size.xy,
            DOUBLEBUF | OPENGL | pg.FULLSCREEN
        )
        # self.font = pg.font.SysFont(None, 24)
        pg.display.set_caption(title)

        # initialize OpenGL stuff
        glClearColor(*(0, 0, 0, 255))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, *global_vars.screen_size.xy, 0)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    @staticmethod
    def set_color(color: Color | tColor) -> Color:
        """
        set gColor
        """
        # color as Color class
        if isinstance(color, Color):
            if color.is_rgba:
                glColor4f(*color.rgba1)

            else:
                glColor3f(*color.rgb1)

            return color

        # color as tuple
        else:
            if len(color) == 3:
                glColor3f(*color)

            elif len(color) == 4:
                glColor4f(*color)

            else:
                raise ValueError("Invalid color: ", color)

            return Color.from_1(*color)

    @staticmethod
    def check_out_of_screen(
            pos,
            size,
    ) -> bool:
        """
        check if a rect is on the screen
        """
        pos = convert_coord(pos, Vec2)
        size = convert_coord(size, Vec2)

        return False

        # 200 for buffering
        return any([
            pos.x > global_vars.screen_size.x + 200,
            pos.x + size.x < -200
        ])

    @staticmethod
    def load_texture(
            image,
            size,
            mirror=""
    ) -> tuple[TextureID, tuple[int, int]]:
        # for debugging
        if size is not None:
            image = image.resize(convert_coord(size))

        if "x" in mirror:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # Flip the image vertically (since OpenGL's origin is at bottom-left)
        if "y" not in mirror:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

        width, height = image.size[0], image.size[1]
        img_data = image.convert("RGBA").tobytes("raw", "RGBA", 0, -1)

        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            img_data
        )
        glEnable(GL_TEXTURE_2D)

        return texture_id, (width, height)

    @staticmethod
    def draw_textured_quad(
            texture_id: TextureID,
            pos,
            size,
            convert_global=True,
            rotate_angle=0
    ):
        pos = convert_coord(pos, Vec2)
        size = convert_coord(size, Vec2)

        # convert to screen realtive coords and size
        if convert_global:
            pos = global_vars.translate_screen_coord(pos)
            size = global_vars.translate_scale(size)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(pos, size):
            return

        # reset color
        glColor3f(1, 1, 1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslate(*pos.xy, 0)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        # rotate
        glRotated(rotate_angle, 0, 0, 1)

        glBegin(GL_QUADS)

        # draw rectangle and texture
        glVertex(0, 0, 0)
        glTexCoord2f(0, 0)
        glVertex(size.x, 0, 0)
        glTexCoord2f(0, 1)
        glVertex(size.x, size.y, 0)
        glTexCoord2f(1, 1)
        glVertex(0, size.y, 0)
        glTexCoord2f(1, 0)

        glEnd()
        glDisable(GL_TEXTURE_2D)
        glFlush()

    def draw_circle(
            self,
            center,
            radius,
            num_segments,
            color,
            convert_global=True
    ):
        center = convert_coord(center, Vec2)

        # convert to screen realtive coords and size
        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(center, (radius, 0)):
            return

        glLoadIdentity()  # reset previous glTranslate statements
        glTranslate(center.x, center.y, 0)

        self.set_color(color)

        glBegin(GL_POLYGON)

        for i in range(num_segments):
            cosine = radius * np.cos(i*2*np.pi / num_segments)
            sine = radius * np.sin(i*2*np.pi / num_segments)
            glVertex2f(cosine, sine)

        glEnd()

    def draw_rect(
            self,
            start,
            size,
            color,
            convert_global=True
    ):
        start = convert_coord(start, Vec2)
        size = convert_coord(size, Vec2)

        if convert_global:
            start = global_vars.translate_screen_coord(start)
            size = global_vars.translate_scale(size)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(start, size):
            return

        glLoadIdentity()  # reset previous glTranslate statements
        glTranslate(start.x, start.y, 0)

        self.set_color(color)

        glBegin(GL_POLYGON)
        glVertex2f(0, 0)
        glVertex2f(size.x, 0)
        glVertex2f(size.x, size.y)
        glVertex2f(0, size.y)
        glEnd()

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

        if convert_global:
            center = global_vars.translate_screen_coord(center)
            radius = global_vars.translate_scale(radius)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(center, (radius + thickness, 0)):
            return

        glLoadIdentity()
        glTranslate(center.x, center.y, 0)

        self.set_color(color)

        for i in range(num_segments):
            i1 = i * 2
            i2 = i1 + 1

            cosine1 = np.cos(i1*2*np.pi / num_segments)
            sine1 = np.sin(i1*2*np.pi / num_segments)

            cosine2 = np.cos(i2*2*np.pi / num_segments)
            sine2 = np.sin(i2*2*np.pi / num_segments)

            glBegin(GL_POLYGON)
            glVertex2f(cosine1 * radius, sine1 * radius)
            glVertex2f(
                cosine1 * (radius + thickness),
                sine1 * (radius + thickness)
            )
            glVertex2f(
                cosine2 * (radius + thickness),
                sine2 * (radius + thickness)
            )
            glVertex2f(cosine2 * radius, sine2 * radius)
            glEnd()

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

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(start, end - start):
            return

        if global_position:
            glLoadIdentity()  # reset previous glTranslate statements

        self.set_color(color)

        glBegin(GL_LINES)
        glVertex2f(*start.xy)
        glVertex2f(*end.xy)
        glEnd()

    def draw_rounded_rect(
            self,
            start,
            size,
            color,
            radius,
    ) -> None:
        start = convert_coord(start, Vec2)
        size = convert_coord(size, Vec2)

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(start, size):
            return

        # circles at edges
        self.draw_circle(
            start + radius,
            radius,
            m.ceil(radius),
            color
        )
        self.draw_circle(
            start + size - radius,
            radius,
            m.ceil(radius),
            color
        )
        self.draw_circle(
            (
                start.x + size.x - radius,
                start.y + radius
            ),
            radius,
            m.ceil(radius),
            color
        )
        self.draw_circle(
            (
                start.x + radius,
                start.y + size.y - radius
            ),
            radius,
            m.ceil(radius),
            color
        )

        # fill in squares
        if size.x > 2 * radius:
            self.draw_rect(
                (
                    start.x + radius,
                    start.y
                ),
                (
                    size.x - 2 * radius,
                    size.y
                ),
                color
            )

        if size.y > 2 * radius:
            self.draw_rect(
                (
                    start.x,
                    start.y + radius
                ),
                (
                    size.x,
                    size.y - 2 * radius
                ),
                color
            )

    def draw_text(
            self,
            pos,
            text,
            color,
            bg_color,
            centered=False,
            font_size=64,
            font_family="arial",
            bold=False,
            italic=False
    ):
        bg_color = self.set_color(bg_color)
        color = self.set_color(color)

        # weird conversion because pygame is ass
        text_surface: pg.Surface = self.generate_pg_surf_text(
            text, color, bg_color, font_size, font_family, bold, italic
        )
        # text_surface.set_alpha(color.a)

        # draw text
        self.draw_pg_surf(pos, text_surface, centered)

        return text_surface.get_size()

    def generate_pg_surf_text(
            self,
            text,
            color,
            bg_color,
            font_size=64,
            font_family="arial",
            bold=False,
            italic=False
    ):
        return self._get_font(
            font_size,
            font_family,
            bold,
            italic
        ).render(
            text,
            True,
            color.rgb255,
            bg_color.rgb255 if bg_color.a > 125 else None
        )

    def draw_pg_surf(self, pos, surface, centered=False):
        pos = convert_coord(pos, Vec2)

        text_data = pg.image.tostring(surface, "RGBA", True)
        text_size: tuple[int, int] = surface.get_size()

        pos.y = global_vars.screen_size.y - pos.y

        if centered:
            pos.x -= text_size[0] / 2
            pos.y -= text_size[1] / 2

        # only draw if on screen
        if OpenGLRenderer.check_out_of_screen(pos, text_size):
            return

        glWindowPos2d(*pos.xy)
        glDrawPixels(
            surface.get_width(),
            surface.get_height(),
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            text_data
        )

