"""
A few functions for rendering.

| ``Path``: amoginarium/graphics/render_bindings/_opengl.py
| ``Project``: amoginarium
| ``Created``: 22.03.2024
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import os

# Stop Windows from minimizing/re-initializing the window if it thinks it lost focus
os.environ["SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS"] = "0"
# Stop Windows DPI scaling from slightly altering the window size and triggering a loop
os.environ["SDL_VIDEO_HIGHDPI_DISABLED"] = "1"

import math as m
import operator
import typing as tp
from collections.abc import Sequence
from types import EllipsisType

import numpy as np
import pygame as pg
from icecream import ic
from OpenGL.GL import GL_ALPHA_TEST, GL_ALWAYS, GL_BLEND, GL_CLAMP_TO_EDGE
from OpenGL.GL import GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_EQUAL, GL_FALSE
from OpenGL.GL import GL_FLOAT, GL_GREATER, GL_KEEP, GL_LINEAR, GL_LINES, GL_MODELVIEW
from OpenGL.GL import GL_NEAREST, GL_ONE_MINUS_SRC_ALPHA, GL_POLYGON, GL_PROJECTION
from OpenGL.GL import GL_QUADS, GL_REPLACE, GL_RGBA, GL_SRC_ALPHA
from OpenGL.GL import GL_STENCIL_BUFFER_BIT, GL_STENCIL_TEST, GL_TEXTURE_2D
from OpenGL.GL import GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_WRAP_S
from OpenGL.GL import GL_TEXTURE_WRAP_T, GL_TRIANGLE_STRIP, GL_TRUE, GL_UNSIGNED_BYTE
from OpenGL.GL import GL_VERTEX_ARRAY, glAlphaFunc, glBegin, glBindTexture, glBlendFunc
from OpenGL.GL import glClear, glClearColor, glColor3f, glColor4f, glColorMask
from OpenGL.GL import glDisable, glDisableClientState, glDrawArrays, glEnable
from OpenGL.GL import glEnableClientState, glEnd, glGenTextures, glLoadIdentity
from OpenGL.GL import glMatrixMode, glOrtho, glPopMatrix, glPushMatrix, glRotated
from OpenGL.GL import glStencilFunc, glStencilMask, glStencilOp, glTexCoord2f
from OpenGL.GL import glTexImage2D, glTexParameteri, glTranslate, glTranslated
from OpenGL.GL import glTranslatef, glVertex2f, glVertexPointer, glViewport
from OpenGL.GLU import gluOrtho2D
from PIL import Image

from amoginarium import pv
from amoginarium.shared.debugging import cum_timer
from amoginarium.shared.utility import Color, convert_color, convert_coord
from amoginarium.shared.utility import fade, normalize_angle, PI_2, Vec2

from ._base_renderer import BaseRenderer
from .opengl_fonts import GLFont
from .windows import WindowsMonitorService

if tp.TYPE_CHECKING:
    from amoginarium.shared.utility import coord_t

    from ._base_renderer import tColor

# define types


# noinspection DuplicatedCode
class OpenGLRenderer(BaseRenderer):  # noqa: PLR0904
    __slots__ = (
        "__dynamic_text_fonts",
        "__static_text_graphics",
        "__static_text_id_counter",
        "__static_text_fonts",
        "__clock",
        "__window",
        "__previous_window_position",
        "__previous_window_size",
    )

    type TextureID = int
    type StaticTextID = int
    type DynamicTextID = int

    DRAW_DEBUG_BOUNDS = False

    __dynamic_text_fonts: dict[tuple[str, int, bool, bool], GLFont]

    __static_text_graphics: dict[StaticTextID, tuple[np.uintc, tuple[int, int]]]
    __static_text_id_counter: StaticTextID
    __static_text_fonts: dict
    __clock: pg.time.Clock
    __window: pg.Window

    __previous_window_position: tp.Final[Vec2]
    __previous_window_size: tp.Final[Vec2]
    __display_state: tp.Literal["windowed", "windowed_fullscreen", "fullscreen"]

    def __init__(self) -> None:
        self.__layer_cache = {}
        super().__init__()

    # region Extra internal methods
    def get_font(
        self, size: int, family: str, bold: bool = False, italic: bool = False
    ) -> pg.font.Font:
        # check if font exists
        if size in self.__static_text_fonts:
            for font in self.__static_text_fonts[size]:
                if all([font.name == family, font.bold == bold, font.italic == italic]):
                    return font

        else:
            self.__static_text_fonts[size] = []

        # no font found, create new
        new_font = pg.font.SysFont(family, int(size), bold, italic)
        self.__static_text_fonts[size].append(new_font)

        return new_font

    @staticmethod
    def __set_color(color: Color | tColor) -> Color:
        """
        Set OpenGLColor
        :param color: Color to set
        :return: The color as a Color object
        :raises ValueError: If a tuple of invalid length is provided
        :raises TypeError: If color is not a Color object or a tuple.
        """
        if isinstance(color, Color):
            glColor4f(*color.rgba1)

            return color
        if isinstance(color, tuple):
            if len(color) == 3:
                glColor3f(*color)
            elif len(color) == 4:
                glColor4f(*color)
            else:
                msg = f"Invalid color tuple length (expected 3 or 4, got {len(color)}): {color}"
                raise ValueError(msg)
            return Color().from_1(*color)
        msg = f"Expected a Color object or a tuple, but got {type(color).__name__}: {color!r}"
        raise TypeError(msg)

    @staticmethod
    @cum_timer.time_this
    def _check_out_of_screen(
        top_left: coord_t,
        size: coord_t,
    ) -> bool:
        """
        Check if a rect is out of the screen.

        :param top_left: Absolute top left position
        :param size: Absolute size
        :return: True if rect is out of screen.
        """
        x1, y1 = convert_coord(top_left)
        w, h = convert_coord(size)

        x2 = x1 + w
        y2 = y1 + h

        if x1 > x2:
            x1, x2 = x2, x1

        if y1 > y2:
            y1, y2 = y2, y1

        res = pv.global_vars.get_resolution()
        return x2 < 0 or x1 > res.x or y2 < 0 or y1 > res.y

    def _draw_debug_bounds(
        self,
        pos: coord_t,
        size: coord_t,
        color: Color | tColor = (255, 0, 0, 127),
        centered: bool = False,
    ) -> None:
        pos_vec: Vec2 = convert_coord(pos, Vec2)
        size_vec: Vec2 = convert_coord(size, Vec2)

        # Handle centering offset
        if centered:
            pos_vec.x -= size_vec.x / 2.0
            pos_vec.y -= size_vec.y / 2.0

        # Hardcode a visible debug thickness and scale it
        thickness = 1

        # Bail out if it's not even on the screen
        if self._check_out_of_screen(pos_vec, size_vec):
            return

        glPushMatrix()
        glTranslate(pos_vec.x, pos_vec.y, 0.0)

        # Set the color natively
        self.__set_color(color)

        # Pre-calculate the inner boundaries for the outline
        ix = size_vec.x - thickness
        iy = size_vec.y - thickness

        # Draw the outline directly via OpenGL
        glBegin(GL_TRIANGLE_STRIP)

        # Trace the hollow frame (Outer vertex, Inner vertex)
        glVertex2f(0.0, 0.0)
        glVertex2f(thickness, thickness)

        glVertex2f(size_vec.x, 0.0)
        glVertex2f(ix, thickness)

        glVertex2f(size_vec.x, size_vec.y)
        glVertex2f(ix, iy)

        glVertex2f(0.0, size_vec.y)
        glVertex2f(thickness, iy)

        # Close the loop
        glVertex2f(0.0, 0.0)
        glVertex2f(thickness, thickness)

        glEnd()
        glPopMatrix()

    @staticmethod
    def __scaling_restricted_ratio(
        size: Vec2, ratio: float
    ) -> tuple[int, int, int, int]:
        window_ratio = size.x / size.y

        if window_ratio > ratio:
            view_h = size.y
            view_w = int(size.y * ratio)
            offset_x = (size.x - view_w) // 2
            offset_y = 0
        else:
            view_w = size.x
            view_h = int(size.x / ratio)
            offset_x = 0
            offset_y = (size.y - view_h) // 2

        return int(offset_x), int(offset_y), int(view_w), int(view_h)

    # endregion

    # region Init & Loading
    def init(self, title: str) -> None:
        """
        Initialize the renderer and global_vars
        :param title: Window title.
        """
        pg.init()
        pv.global_vars = pv.global_vars

        ic("using OpenGL backend")

        pg.font.init()

        # Text
        self.__dynamic_text_fonts = {}
        self.__static_text_graphics = {}
        self.__static_text_id_counter = 0

        self.__previous_window_size = Vec2().from_cartesian(1920, 1080)
        self.__previous_window_position = Vec2()

        self.__static_text_fonts = {
            32: [pg.font.SysFont("arial", 32)],
            64: [pg.font.SysFont("arial", 64)],
        }

        # get screen size
        screen_info = pg.display.Info()
        window_size = (
            1920,
            1080,
        )  # (screen_info.current_w, screen_info.current_h)  # TODO: sizing

        # set global screen size and ppm
        pv.global_vars.set_screen_size(Vec2().from_cartesian(*window_size))
        pv.global_vars.set_screen_size_real(
            Vec2().from_cartesian(screen_info.current_w, screen_info.current_h)
        )
        pv.global_vars.set_resolution(Vec2().from_cartesian(*window_size))

        screen_fac = Vec2().from_cartesian(1, 1)
        screen_offset = Vec2().from_cartesian(0, 0)

        pv.global_vars.set_screen_size_fac(screen_fac)
        pv.global_vars.set_screen_size_offset(screen_offset)
        pv.global_vars.set_pixel_per_meter(1)

        # set max fps to monitor refresh rate
        pv.global_vars.set_max_fps(max(pg.display.get_desktop_refresh_rates()))

        # pg.display.gl_set_attribute(pg.GL_SWAP_CONTROL, 1)
        pg.display.gl_set_attribute(pg.GL_RED_SIZE, 8)
        pg.display.gl_set_attribute(pg.GL_GREEN_SIZE, 8)
        pg.display.gl_set_attribute(pg.GL_BLUE_SIZE, 8)
        pg.display.gl_set_attribute(pg.GL_ALPHA_SIZE, 8)
        pg.display.gl_set_attribute(pg.GL_STENCIL_SIZE, 8)

        # pg window
        screen_size = pv.global_vars.get_screen_size()
        self.__window = pg.Window(
            title=title,
            size=(screen_size.x / 2, screen_size.y / 2),
            opengl=True,
            resizable=True,
            hidden=True,
        )
        self.__window.minimum_size = ((screen_size.x / 8, screen_size.y / 8),)
        WindowsMonitorService.set_window(title)

        # initialize OpenGL stuff
        glClearColor(*(0, 0, 0, 255))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, *pv.global_vars.get_screen_size().xy, 0)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.__clock = pg.time.Clock()

        self.__window.show()
        self.__display_state = "windowed"

    def quit(self) -> None:
        """
        Quit the display.
        """
        pg.quit()

    def load_texture(
        self,
        image: Image.Image,
        size: coord_t | None = None,
        mirror: tp.Literal["x", "y", "xy", "yx", ""] = "",
        pixel_perfect: bool = False,
    ) -> tuple[TextureID, tuple[int, int]]:
        """
        Load an image texture (saves it internally)
        :param image: Image to load
        :param size: Size of image or None
        :param mirror: Axes to mirror the image on
        :param pixel_perfect: set texture scaling behavior
        :returns: integer texture id, (width, height).
        """
        if size is not None:
            if image.size != (target_size := convert_coord(size, int)):
                image = image.resize(target_size, resample=Image.Resampling.NEAREST)

        if mirror == "":
            image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        elif mirror == "x":
            image = image.transpose(Image.Transpose.ROTATE_180)
        elif mirror in ("xy", "yx"):
            image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        width, height = image.size[0], image.size[1]
        # noinspection PyArgumentEqualDefault
        img_data = image.tobytes("raw", "RGBA", 0, -1)

        # noinspection PyArgumentList
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        # set scaling behavior
        if pixel_perfect:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            img_data,
        )

        return texture_id, (width, height)

    # endregion

    # region Display
    @property
    def display_state(
        self,
    ) -> tp.Literal["windowed", "fullscreen", "windowed_fullscreen"]:
        return self.__display_state

    def clear_display(self, color: Color | tColor = (0, 0, 0, 0)) -> None:
        """
        Clear the whole window
        :param color: Color to clear the window with.
        """
        conv_color: Color = convert_color(color, Color)
        glClearColor(*conv_color.rgba1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def display_update(
        self, position: coord_t | None = None, size: coord_t | None = None
    ) -> None:
        """
        Should be called when the display gets updated
        :param position: Position of the display
        :param size: Size of the display.
        """
        if self.__display_state in ["fullscreen", "windowed_fullscreen"]:
            self.__window.restore()
            self.__window.borderless = False
            self.__window.set_windowed()
            self.__window.size = self.__previous_window_size.xy
            self.__window.maximize()
            self.__display_state = "windowed"

        if position is None:
            position = self.__window.position
        if size is None:
            size = self.__window.size

        _position_vec: Vec2 = convert_coord(position, Vec2)
        size_vec: Vec2 = convert_coord(size, Vec2)

        res_x, res_y = pv.global_vars.get_resolution().xy
        res_ratio = res_x / res_y

        vp_x, vp_y, vp_w, vp_h = self.__scaling_restricted_ratio(size_vec, res_ratio)

        scaling = pv.global_vars.get_scaling()

        if scaling == 0:
            # 1. Resize the window native way
            self.__window.size = (int(size_vec.x), int(size_vec.y))
            # 2. Update viewport
            glViewport(vp_x, vp_y, vp_w, vp_h)

            pv.global_vars.set_screen_size_real(convert_coord(size_vec, Vec2))

            pv.global_vars.set_screen_size_fac(
                Vec2().from_cartesian(res_x / vp_w, res_y / vp_h)
            )
            pv.global_vars.set_screen_size_offset(Vec2().from_cartesian(vp_x, vp_y))

        elif scaling == 1:
            self.__window.size = (vp_w, vp_h)
            glViewport(0, 0, vp_w, vp_h)

            s_size_real = convert_coord((vp_w, vp_h), Vec2)
            pv.global_vars.set_screen_size_real(s_size_real)

            pv.global_vars.set_screen_size_fac(
                Vec2().from_cartesian(res_x / s_size_real.x, res_y / s_size_real.y)
            )
            pv.global_vars.set_screen_size_offset(Vec2().from_cartesian(0, 0))

        else:
            self.__window.size = (int(size_vec.x), int(size_vec.y))
            glViewport(0, 0, int(size_vec.x), int(size_vec.y))

            pv.global_vars.set_screen_size_real(size_vec)

            pv.global_vars.set_screen_size_fac(
                Vec2().from_cartesian(res_x / size_vec.x, res_y / size_vec.y)
            )
            pv.global_vars.set_screen_size_offset(Vec2().from_cartesian(0, 0))

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        glOrtho(0, res_x, res_y, 0, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def display_get_geometry(self) -> tuple[Vec2, Vec2]:
        """
        Change the position and size of the display
        :return: (position, size) of the window.
        """
        pos_x, pos_y = self.__window.position
        size_w, size_h = self.__window.size

        return (
            Vec2().from_cartesian(pos_x, pos_y),
            Vec2().from_cartesian(size_w, size_h),
        )

    def display_set_geometry(self, position: coord_t, size: coord_t) -> None:
        """
        Change the position and size of the display
        :param position: New position
        :param size: New size.
        """
        self.__window.set_windowed()

        pos_tuple = convert_coord(position, tuple)
        size_tuple = convert_coord(size, tuple)

        self.__window.position = (int(pos_tuple[0]), int(pos_tuple[1]))
        self.__window.size = (int(size_tuple[0]), int(size_tuple[1]))

    def __display_save_geometry(self) -> None:
        self.__previous_window_size.xy = self.__window.size
        self.__previous_window_position.xy = self.__window.position

    def display_fullscreen(self) -> None:
        """
        Activate fullscreen mode.
        """
        self.__display_save_geometry()
        self.__window.set_fullscreen(True)
        self.display_update()
        self.__display_state = "fullscreen"

    def display_windowed_fullscreen(self) -> None:
        """
        Activate windowed fullscreen mode.
        """
        self.__display_save_geometry()
        pos, size, combined = WindowsMonitorService.get_current_monitor_combined()
        self.__window.borderless = True
        self.__window.position = pos.xy
        # +1 is needed is here, because otherwise Windows will convert it to a normal fullscreen xD
        self.__window.size = size.x, size.y + (0 if combined else 1)

        self.display_update()
        self.__display_state = "windowed_fullscreen"

    def display_set_windowed(self) -> None:
        self.__display_state = "windowed"
        self.__window.set_windowed()
        self.__window.borderless = False
        self.display_set_geometry(
            self.__previous_window_position, self.__previous_window_size
        )
        self.display_update(
            self.__previous_window_position.xy, self.__previous_window_size.xy
        )

    def display_set_title(self, title: str, icon: str | None = None) -> None:
        """
        Set the caption/titlebar of the display
        :param title: String title
        :param icon: Icon.
        """
        self.__window.title = title

    def display_draw_frame(self) -> None:
        """
        Called each frame after the drawing.
        """
        self.__window.flip()
        self.__clock.tick(pv.global_vars.get_max_fps())

    # endregion

    # region Stencil
    def apply_stencil[**A](
        self,
        stencil_func: tp.Callable[A, tp.Any],
        show_stencil=False,
        *args: A.args,
        **kwargs: A.kwargs,
    ) -> None:
        self.start_stencil(show_stencil)

        stencil_func(*args, **kwargs)

        self.enable_stencil(show_stencil)

    def start_stencil(self, show_stencil=False) -> None:
        """
        Call this, then draw stencil, then draw enable_stencil.
        """
        glEnable(GL_STENCIL_TEST)
        glClear(GL_STENCIL_BUFFER_BIT)

        glStencilFunc(GL_ALWAYS, 1, 0xFF)
        glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE)
        glStencilMask(0xFF)

        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.01)

        if not show_stencil:
            glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)  # if mask invis

    def enable_stencil(self, show_stencil=False) -> None:
        """
        start_stencil must be called first.
        """
        if not show_stencil:
            glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

        glStencilMask(0x00)
        glStencilFunc(GL_EQUAL, 1, 0xFF)

    def disable_stencil(self) -> None:
        glDisable(GL_STENCIL_TEST)
        glStencilMask(0xFF)
        glStencilFunc(GL_ALWAYS, 0, 0xFF)

    # endregion

    # region Textured
    def draw_textured_quad(
        self,
        texture_id: TextureID,
        pos: coord_t,
        size: coord_t,
        layer: int,
        *,
        convert_global: bool = True,
        rotate_angle: float = 0,
        rotate_anchor: coord_t | EllipsisType = ...,
        offscreen_check: bool = True,
        force_draw: bool = False,
        color: Color | EllipsisType = ...,
    ) -> None:
        """
        Draw a rectangle with a texture
        :param texture_id: ID of the texture to draw
        :param pos: Absolute position on window
        :param size: Absolute size on window
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param rotate_angle: Angle in degrees to rotate the image at
        :param rotate_anchor: What pixel to rotate at. Defaults to center position
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :param layer: Layer number
        :param force_draw: force the renderer to draw the quad NOW (only use for stencils)
        :param color: overlay color to tint the quad.
        """
        pos_vec2: Vec2 = convert_coord(pos, Vec2)  # type: ignore
        size_vec2: Vec2 = convert_coord(size, Vec2)  # type: ignore

        if convert_global:
            pos_vec2 = pv.global_vars.translate_screen_coord(pos_vec2)
            size_vec2 = pv.global_vars.translate_scale(size_vec2)

        if offscreen_check and self._check_out_of_screen(pos_vec2, size_vec2):
            return

        if layer not in self.__layer_cache:
            self.__layer_cache[layer] = []

        # rotate
        rx = 0
        ry = 0
        if rotate_angle != 0.0:
            if isinstance(rotate_anchor, EllipsisType):
                rx, ry = size_vec2.x / 2.0, size_vec2.y / 2.0
            else:
                anchor: Vec2 = convert_coord(  # type: ignore
                    rotate_anchor, Vec2
                )

                if convert_global:
                    anchor = pv.global_vars.translate_scale(anchor)

                rx, ry = anchor.x, anchor.y

        draw_info: dict[str, tp.Any] = {
            "texture_id": texture_id,
            "pos": pos_vec2,
            "size": size_vec2,
            "rotate_angle": rotate_angle,
            "rotate_anchor": (rx, ry),
        }

        if not isinstance(color, EllipsisType):
            draw_info["color"] = color

        if force_draw:
            self.__draw_layer([draw_info])

        else:
            self.__layer_cache[layer].append(draw_info)

    def __draw_layer(self, layer: list[dict[str, tp.Any]]) -> None:
        """Draw one texture layer."""
        layer = sorted(layer, key=operator.itemgetter("texture_id"))

        # reset color
        glColor3f(1.0, 1.0, 1.0)

        current_texture = -1
        for sprite in layer:
            pos: Vec2 = sprite["pos"]
            size: Vec2 = sprite["size"]

            texture_id: int = sprite["texture_id"]

            rotate_angle: float = sprite["rotate_angle"]
            rx, ry = sprite["rotate_anchor"]

            if "color" in sprite:
                self.__set_color(sprite["color"])

            glPushMatrix()
            glTranslate(pos.x, pos.y, 0.0)

            # only re-bind texture on sprite type change
            if texture_id != current_texture:
                glBindTexture(GL_TEXTURE_2D, texture_id)
                current_texture = texture_id

            glEnable(GL_TEXTURE_2D)

            if rotate_angle != 0.0:
                glTranslated(rx, ry, 0.0)
                glRotated(rotate_angle, 0.0, 0.0, 1.0)
                glTranslated(-rx, -ry, 0.0)

            glBegin(GL_QUADS)

            # draw rectangle and texture
            glTexCoord2f(1.0, 0.0)
            glVertex2f(0.0, 0.0)
            glTexCoord2f(0.0, 0.0)
            glVertex2f(size.x, 0.0)
            glTexCoord2f(0.0, 1.0)
            glVertex2f(size.x, size.y)
            glTexCoord2f(1.0, 1.0)
            glVertex2f(0.0, size.y)

            glEnd()
            glDisable(GL_TEXTURE_2D)
            glPopMatrix()

            if "color" in sprite:  # reset color
                glColor3f(1.0, 1.0, 1.0)

            if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
                self._draw_debug_bounds(pos, size)

    def flush_layer(self, layer: int) -> None:
        # get layer from cache and delete
        sprites = self.__layer_cache.pop(layer, [])

        # draw layer
        self.__draw_layer(sprites)

    def flush(self) -> None:
        layers = self.__layer_cache.copy().keys()
        layers = sorted(layers)

        # sort cache by texture_id, pixel perfect
        for layer_id in sorted(layers):
            self.__draw_layer(self.__layer_cache.pop(layer_id))

    # endregion

    # region Basic shapes
    def draw_polygon(
        self,
        vertices: tp.Iterable[coord_t],
        color: Color | tColor,
        *,
        center: coord_t = None,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a polygon with fill
        :param vertices: Coord of the corner points of the polygon
        :param color: Drawing color
        :param center: Optional center position
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: NOT SUPPORTED.
        """
        vertices_vec2: list[Vec2] = [convert_coord(v, Vec2) for v in vertices]

        if convert_global:
            if center:
                vertices_vec2 = [
                    pv.global_vars.translate_scale(v) for v in vertices_vec2
                ]

            else:
                vertices_vec2 = [
                    pv.global_vars.translate_screen_coord(v) for v in vertices_vec2
                ]

        glPushMatrix()
        if center is not None:
            center_vec2: Vec2 = convert_coord(center, Vec2)
            if convert_global:
                center_vec2 = pv.global_vars.translate_screen_coord(center_vec2)

            glTranslate(center_vec2.x, center_vec2.y, 0)

        self.__set_color(color)

        glBegin(GL_POLYGON)

        for vertice in vertices_vec2:
            glVertex2f(vertice.x, vertice.y)

        glEnd()
        glPopMatrix()

    def draw_polygon_line(
        self,
        vertices: tp.Iterable[coord_t],
        color: Color | tColor | Sequence[Color | tColor],
        *,
        thickness: float = 1.0,
        center: coord_t = None,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a polygon outline without fill
        :param vertices: Coord of the corner points of the polygon
        :param color: Drawing color
        :param thickness: Thickness of the outline
        :param center: Optional center position
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: NOT SUPPORTED.
        """
        vertices_vec2: list[Vec2] = [convert_coord(v, Vec2) for v in vertices]
        if not vertices_vec2:
            return

        if convert_global:
            thickness = pv.global_vars.translate_scale(thickness)
            if center:
                vertices_vec2 = [
                    pv.global_vars.translate_scale(v) for v in vertices_vec2
                ]
            else:
                vertices_vec2 = [
                    pv.global_vars.translate_screen_coord(v) for v in vertices_vec2
                ]

        glPushMatrix()
        if center is not None:
            center_vec2: Vec2 = convert_coord(center, Vec2)
            if convert_global:
                center_vec2 = pv.global_vars.translate_screen_coord(center_vec2)
            glTranslate(center_vec2.x, center_vec2.y, 0)

        # set color if single color is given
        self.__set_color(color)

        # Use TRIANGLE_STRIP to create a thick outline by calculating offsets for
        # each segment
        glBegin(GL_TRIANGLE_STRIP)
        num_verts = len(vertices_vec2)
        for i in range(num_verts + 1):
            v1 = vertices_vec2[i % num_verts]
            v2 = vertices_vec2[(i + 1) % num_verts]

            dx, dy = v2.x - v1.x, v2.y - v1.y
            length = m.hypot(dx, dy)
            if length == 0:
                continue

            off_x = (-dy / length) * (thickness * 0.5)
            off_y = (dx / length) * (thickness * 0.5)

            glVertex2f(v1.x + off_x, v1.y + off_y)
            glVertex2f(v1.x - off_x, v1.y - off_y)

        glEnd()
        glPopMatrix()

    def draw_rect(
        self,
        start: coord_t,
        size: coord_t,
        color: Color | tColor,
        *,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a rectangle with fill
        :param start: Absolute top left corner position
        :param size: Width and height of the rectangle
        :param color: Drawing color
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        start_vec2: Vec2 = convert_coord(start, Vec2)
        size_vec2: Vec2 = convert_coord(size, Vec2)

        if convert_global:
            start_vec2 = pv.global_vars.translate_screen_coord(start_vec2)
            size_vec2 = pv.global_vars.translate_scale(size_vec2)

        if offscreen_check and self._check_out_of_screen(start_vec2, size_vec2):
            return

        glPushMatrix()
        glTranslate(start_vec2.x, start_vec2.y, 0.0)

        self.__set_color(color)

        glBegin(GL_QUADS)
        glVertex2f(0.0, 0.0)
        glVertex2f(size_vec2.x, 0.0)
        glVertex2f(size_vec2.x, size_vec2.y)
        glVertex2f(0.0, size_vec2.y)
        glEnd()
        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(start_vec2, size_vec2)

    @cum_timer.time_this
    def draw_rounded_rect(
        self,
        start: coord_t,
        size: coord_t,
        color: Color | tColor,
        radius: float,
        *,
        top_left_radius: float | None = None,
        top_right_radius: float | None = None,
        bottom_left_radius: float | None = None,
        bottom_right_radius: float | None = None,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a rect with rounded corners with fill.

        :param start: Absolute top left corner position
        :param size: Width and height of the rectangle
        :param color: Drawing color
        :param radius: Radius of the corners
        :param top_left_radius: Individual radius for the top left corner. Defaults to radius
        :param top_right_radius: Individual radius for the top right corner. Defaults to radius
        :param bottom_left_radius: Individual radius for the bottom left corner. Defaults to radius
        :param bottom_right_radius: Individual radius for the bottom right corner. Defaults to radius
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        start_vec: Vec2 = convert_coord(start, Vec2)
        size_vec: Vec2 = convert_coord(size, Vec2)

        if convert_global:
            start_vec = pv.global_vars.translate_screen_coord(start_vec)
            size_vec = pv.global_vars.translate_scale(size_vec)
            radius = pv.global_vars.translate_scale(radius)
            if top_left_radius is not None:
                top_left_radius = pv.global_vars.translate_scale(top_left_radius)
            if top_right_radius is not None:
                top_right_radius = pv.global_vars.translate_scale(top_right_radius)
            if bottom_right_radius is not None:
                bottom_right_radius = pv.global_vars.translate_scale(
                    bottom_right_radius
                )
            if bottom_left_radius is not None:
                bottom_left_radius = pv.global_vars.translate_scale(bottom_left_radius)

        sx, sy = size_vec.x, size_vec.y

        if offscreen_check and self._check_out_of_screen(start_vec, size_vec):
            return

        r_tl = radius if top_left_radius is None else top_left_radius
        r_tr = radius if top_right_radius is None else top_right_radius
        r_br = radius if bottom_right_radius is None else bottom_right_radius
        r_bl = radius if bottom_left_radius is None else bottom_left_radius

        max_rad = min(sx / 2.0, sy / 2.0)
        r_tl = min(r_tl, max_rad)
        r_tr = min(r_tr, max_rad)
        r_br = min(r_br, max_rad)
        r_bl = min(r_bl, max_rad)

        glPushMatrix()
        glTranslate(start_vec.x, start_vec.y, 0.0)
        self.__set_color(color)

        glBegin(GL_POLYGON)
        v2f = glVertex2f

        if r_tl == r_tr == r_br == r_bl:
            rad = r_tl
            segments = max(4, int(rad / 2.0))
            step = 1.5707963267948966 / segments
            base_arc = [
                (m.cos(i * step) * rad, m.sin(i * step) * rad)
                for i in range(segments + 1)
            ]

            [v2f(rad - x, rad - y) for x, y in base_arc]
            [v2f(sx - rad + y, rad - x) for x, y in base_arc]
            [v2f(sx - rad + x, sy - rad + y) for x, y in base_arc]
            [v2f(rad - y, sy - rad + x) for x, y in base_arc]

        else:
            s_tl = max(4, int(r_tl / 2.0))
            st_tl = 1.5707963267948966 / s_tl
            arc_tl = [
                (m.cos(i * st_tl) * r_tl, m.sin(i * st_tl) * r_tl)
                for i in range(s_tl + 1)
            ]
            [v2f(r_tl - x, r_tl - y) for x, y in arc_tl]

            s_tr = max(4, int(r_tr / 2.0))
            st_tr = 1.5707963267948966 / s_tr
            arc_tr = [
                (m.cos(i * st_tr) * r_tr, m.sin(i * st_tr) * r_tr)
                for i in range(s_tr + 1)
            ]
            [v2f(sx - r_tr + y, r_tr - x) for x, y in arc_tr]

            s_br = max(4, int(r_br / 2.0))
            st_br = 1.5707963267948966 / s_br
            arc_br = [
                (m.cos(i * st_br) * r_br, m.sin(i * st_br) * r_br)
                for i in range(s_br + 1)
            ]
            [v2f(sx - r_br + x, sy - r_br + y) for x, y in arc_br]

            s_bl = max(4, int(r_bl / 2.0))
            st_bl = 1.5707963267948966 / s_bl
            arc_bl = [
                (m.cos(i * st_bl) * r_bl, m.sin(i * st_bl) * r_bl)
                for i in range(s_bl + 1)
            ]
            [v2f(r_bl - y, sy - r_bl + x) for x, y in arc_bl]

        glEnd()
        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(start_vec, size_vec)

    def draw_rect_line(
        self,
        start: coord_t,
        size: coord_t,
        color: Color | tColor,
        *,
        thickness: float = 1.0,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a rectangle outline without fill.

        :param start: Absolute top left corner position
        :param size: Width and height of the rectangle
        :param color: Drawing color
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        start_vec: Vec2 = convert_coord(start, Vec2)
        size_vec: Vec2 = convert_coord(size, Vec2)

        if convert_global:
            start_vec = pv.global_vars.translate_screen_coord(start_vec)
            size_vec = pv.global_vars.translate_scale(size_vec)
            thickness = pv.global_vars.translate_scale(thickness)

        if offscreen_check and self._check_out_of_screen(start_vec, size_vec):
            return

        glPushMatrix()
        glTranslate(start_vec.x, start_vec.y, 0.0)
        self.__set_color(color)

        # Pre-calculate the inner boundaries
        ix = size_vec.x - thickness
        iy = size_vec.y - thickness

        glBegin(GL_TRIANGLE_STRIP)

        # Trace the hollow frame (Outer vertex, Inner vertex)
        glVertex2f(0.0, 0.0)
        glVertex2f(thickness, thickness)

        glVertex2f(size_vec.x, 0.0)
        glVertex2f(ix, thickness)

        glVertex2f(size_vec.x, size_vec.y)
        glVertex2f(ix, iy)

        glVertex2f(0.0, size_vec.y)
        glVertex2f(thickness, iy)

        # Close the loop
        glVertex2f(0.0, 0.0)
        glVertex2f(thickness, thickness)

        glEnd()
        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(start_vec, size_vec)

    def draw_rounded_rect_line(
        self,
        start: coord_t,
        size: coord_t,
        color: Color | tColor,
        radius: float,
        *,
        top_left_radius: float | None = None,
        top_right_radius: float | None = None,
        bottom_left_radius: float | None = None,
        bottom_right_radius: float | None = None,
        thickness: float = 1.0,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a rounded rectangle outline without fill
        :param start: Absolute top left corner position
        :param size: Width and height of the rectangle
        :param color: Drawing color
        :param radius: Radius of the corners
        :param top_left_radius: Individual radius for the top left corner. Defaults to radius
        :param top_right_radius: Individual radius for the top right corner. Defaults to radius
        :param bottom_left_radius: Individual radius for the bottom left corner. Defaults to radius
        :param bottom_right_radius: Individual radius for the bottom right corner. Defaults to radius
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        start_vec: Vec2 = convert_coord(start, Vec2)
        size_vec: Vec2 = convert_coord(size, Vec2)

        if convert_global:
            start_vec = pv.global_vars.translate_screen_coord(start_vec)
            size_vec = pv.global_vars.translate_scale(size_vec)
            radius = pv.global_vars.translate_scale(radius)
            thickness = pv.global_vars.translate_scale(thickness)
            if top_left_radius is not None:
                top_left_radius = pv.global_vars.translate_scale(top_left_radius)
            if top_right_radius is not None:
                top_right_radius = pv.global_vars.translate_scale(top_right_radius)
            if bottom_left_radius is not None:
                bottom_left_radius = pv.global_vars.translate_scale(bottom_left_radius)
            if bottom_right_radius is not None:
                bottom_right_radius = pv.global_vars.translate_scale(
                    bottom_right_radius
                )

        sx = size_vec.x
        sy = size_vec.y

        if offscreen_check and self._check_out_of_screen(start_vec, size_vec):
            return

        r_tl = min(
            radius if top_left_radius is None else top_left_radius, sx / 2.0, sy / 2.0
        )
        r_tr = min(
            radius if top_right_radius is None else top_right_radius, sx / 2.0, sy / 2.0
        )
        r_bl = min(
            radius if bottom_left_radius is None else bottom_left_radius,
            sx / 2.0,
            sy / 2.0,
        )
        r_br = min(
            radius if bottom_right_radius is None else bottom_right_radius,
            sx / 2.0,
            sy / 2.0,
        )

        glPushMatrix()
        glTranslate(start_vec.x, start_vec.y, 0.0)
        self.__set_color(color)

        s_tl = max(4, int(r_tl / 2.0))
        s_tr = max(4, int(r_tr / 2.0))
        s_br = max(4, int(r_br / 2.0))
        s_bl = max(4, int(r_bl / 2.0))

        verts = np.empty(((s_tl + s_tr + s_br + s_bl + 4) * 2 + 2, 2), dtype=np.float32)
        idx = 0

        a_tl = np.linspace(np.pi, 1.5 * np.pi, s_tl + 1)
        c_tl = np.cos(a_tl)
        s_tl_a = np.sin(a_tl)
        in_tl = max(0.0, r_tl - thickness)
        verts[idx : idx + len(a_tl) * 2 : 2, 0] = r_tl + c_tl * r_tl
        verts[idx : idx + len(a_tl) * 2 : 2, 1] = r_tl + s_tl_a * r_tl
        verts[idx + 1 : idx + len(a_tl) * 2 : 2, 0] = r_tl + c_tl * in_tl
        verts[idx + 1 : idx + len(a_tl) * 2 : 2, 1] = r_tl + s_tl_a * in_tl
        idx += len(a_tl) * 2

        a_tr = np.linspace(1.5 * np.pi, 2.0 * np.pi, s_tr + 1)
        c_tr = np.cos(a_tr)
        s_tr_a = np.sin(a_tr)
        in_tr = max(0.0, r_tr - thickness)
        verts[idx : idx + len(a_tr) * 2 : 2, 0] = sx - r_tr + c_tr * r_tr
        verts[idx : idx + len(a_tr) * 2 : 2, 1] = r_tr + s_tr_a * r_tr
        verts[idx + 1 : idx + len(a_tr) * 2 : 2, 0] = sx - r_tr + c_tr * in_tr
        verts[idx + 1 : idx + len(a_tr) * 2 : 2, 1] = r_tr + s_tr_a * in_tr
        idx += len(a_tr) * 2

        a_br = np.linspace(0.0, 0.5 * np.pi, s_br + 1)
        c_br = np.cos(a_br)
        s_br_a = np.sin(a_br)
        in_br = max(0.0, r_br - thickness)
        verts[idx : idx + len(a_br) * 2 : 2, 0] = sx - r_br + c_br * r_br
        verts[idx : idx + len(a_br) * 2 : 2, 1] = sy - r_br + s_br_a * r_br
        verts[idx + 1 : idx + len(a_br) * 2 : 2, 0] = sx - r_br + c_br * in_br
        verts[idx + 1 : idx + len(a_br) * 2 : 2, 1] = sy - r_br + s_br_a * in_br
        idx += len(a_br) * 2

        a_bl = np.linspace(0.5 * np.pi, np.pi, s_bl + 1)
        c_bl = np.cos(a_bl)
        s_bl_a = np.sin(a_bl)
        in_bl = max(0.0, r_bl - thickness)
        verts[idx : idx + len(a_bl) * 2 : 2, 0] = r_bl + c_bl * r_bl
        verts[idx : idx + len(a_bl) * 2 : 2, 1] = sy - r_bl + s_bl_a * r_bl
        verts[idx + 1 : idx + len(a_bl) * 2 : 2, 0] = r_bl + c_bl * in_bl
        verts[idx + 1 : idx + len(a_bl) * 2 : 2, 1] = sy - r_bl + s_bl_a * in_bl
        idx += len(a_bl) * 2

        verts[idx, 0] = 0.0
        verts[idx, 1] = r_tl
        verts[idx + 1, 0] = r_tl - max(0.0, r_tl - thickness)
        verts[idx + 1, 1] = r_tl

        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, verts)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, len(verts))
        glDisableClientState(GL_VERTEX_ARRAY)

        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(start_vec, size_vec)

    def draw_bar(
        self,
        pos: coord_t,
        size: coord_t,
        colors: tuple[Color, Color, Color] | tuple[Color, Color] | tuple[Color],
        progress: float,
        *,
        background_color: Color | EllipsisType = ...,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a progress? bar at the specified location (using specified color gradient.
        """
        pos: Vec2 = convert_coord(pos, Vec2)  # ignore: type
        size: Vec2 = convert_coord(size, Vec2)  # ignore: type

        if len(colors) == 1:
            color: Color = colors[0]

        elif len(colors) == 2:
            color: Color = fade(colors[0], colors[1], progress)  # ignore: type

        elif len(colors) == 3:
            color: Color = (
                fade(colors[0], colors[1], progress)
                if progress < 0.5
                else fade(colors[1], colors[2], progress)
            )  # ignore: type

        else:
            msg = f'Invalid colors for "draw_bar": {colors}'
            raise RuntimeError(msg)

        if isinstance(background_color, EllipsisType):
            background_color: Color = Color().from_1(0, 0, 0, 0.5)

        if convert_global:
            pos = pv.global_vars.translate_screen_coord(pos)
            size = pv.global_vars.translate_scale(size)

        glPushMatrix()  # reset previous glTranslate statements
        glTranslate(pos.x, pos.y, 0)

        # draw progress
        self.__set_color(color)

        glBegin(GL_POLYGON)
        glVertex2f(0, 0)
        glVertex2f(size.x * progress, 0)
        glVertex2f(size.x * progress, size.y)
        glVertex2f(0, size.y)
        glEnd()

        # draw background bar
        self.__set_color(background_color)

        glBegin(GL_POLYGON)
        glVertex2f(size.x * progress, 0)
        glVertex2f(size.x, 0)
        glVertex2f(size.x, size.y)
        glVertex2f(size.x * progress, size.y)
        glEnd()

        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(pos, size)

    # endregion

    # region Circles
    def draw_circle(
        self,
        center: coord_t,
        radius: float,
        num_segments: int,
        color: Color | tColor,
        *,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a circle with fil
        :param center: Absolute center position
        :param radius: Radius of the circle in pixels
        :param num_segments: Number of segments
        :param color: Drawing color
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing (rect check).
        """
        center_vec2: Vec2 = convert_coord(center, Vec2)

        if convert_global:
            center_vec2 = pv.global_vars.translate_screen_coord(center_vec2)
            radius = pv.global_vars.translate_scale(radius)

        if offscreen_check and self._check_out_of_screen(
            (center_vec2.x - radius, center_vec2.y - radius), (radius * 2, radius * 2)
        ):
            return

        glPushMatrix()
        glTranslate(center_vec2.x, center_vec2.y, 0.0)

        self.__set_color(color)

        glBegin(GL_POLYGON)

        step = m.tau / num_segments
        [
            glVertex2f(radius * m.cos(i * step), radius * m.sin(i * step))
            for i in range(num_segments)
        ]

        glEnd()
        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(
                center_vec2, (radius * 2, radius * 2), centered=True
            )

    def draw_line_circle(
        self,
        center: coord_t,
        radius: float,
        num_segments: int,
        color: Color | tColor,
        *,
        thickness: float = 1.0,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a circle outline
        :param center: Absolute center position
        :param radius: Radius of the circle in pixels
        :param num_segments: Number of segments
        :param color: Drawing color
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        center_vec2: Vec2 = convert_coord(center, Vec2)

        if convert_global:
            center_vec2 = pv.global_vars.translate_screen_coord(center_vec2)
            radius = pv.global_vars.translate_scale(radius)
            thickness = pv.global_vars.translate_scale(thickness)

        outer: float = radius + thickness
        if offscreen_check and self._check_out_of_screen(
            (center_vec2.x - outer, center_vec2.y - outer), (outer * 2, outer * 2)
        ):
            return

        glPushMatrix()
        glTranslate(center_vec2.x, center_vec2.y, 0.0)

        self.__set_color(color)

        glBegin(GL_TRIANGLE_STRIP)

        step: float = m.tau / num_segments
        [
            (glVertex2f(outer * c, outer * s), glVertex2f(radius * c, radius * s))
            for i in range(num_segments + 1)
            for c in (m.cos(i * step),)
            for s in (m.sin(i * step),)
        ]

        glEnd()
        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(
                center_vec2, (radius * 2, radius * 2), centered=True
            )

    def draw_partial_circle(
        self,
        center: coord_t,
        radius: float,
        angle_start: coord_t,
        angle_end: coord_t,
        num_segments: int,
        color: Color | tColor,
        *,
        convert_global=True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a partial circle with fill
        :param center: Absolute center position
        :param radius: Radius of the circle in pixels
        :param angle_start: Angle to start at as vector
        :param angle_end: Angle to end at as vector
        :param num_segments: Number of segments
        :param color: Drawing color
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        center_vec2: Vec2 = convert_coord(center, Vec2)
        angle_start_vec2: Vec2 = convert_coord(angle_start, Vec2)
        angle_end_vec2: Vec2 = convert_coord(angle_end, Vec2)

        if convert_global:
            center_vec2 = pv.global_vars.translate_screen_coord(center_vec2)
            radius = pv.global_vars.translate_scale(radius)

        if offscreen_check and self._check_out_of_screen(
            (center_vec2.x - radius, center_vec2.y - radius), (radius * 2, radius * 2)
        ):
            return

        angle_delta: float = normalize_angle(angle_end_vec2.angle) - normalize_angle(
            angle_start_vec2.angle
        )

        glPushMatrix()
        glTranslate(center_vec2.x, center_vec2.y, 0.0)

        self.__set_color(color)

        glBegin(GL_POLYGON)
        glVertex2f(0.0, 0.0)

        start_ang = angle_start_vec2.angle
        step = angle_delta / num_segments

        [
            glVertex2f(
                radius * m.cos(start_ang + i * step),
                radius * m.sin(start_ang + i * step),
            )
            for i in range(num_segments + 1)
        ]

        glEnd()
        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(
                center_vec2, (radius * 2, radius * 2), centered=True
            )

    @cum_timer.time_this
    def draw_dashed_circle(
        self,
        center: coord_t,
        radius: float,
        num_segments: int,
        color: Color | tColor,
        *,
        draw_len: int = 1,
        gap_len: int = 1,
        thickness: int = 1,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a dashed circle line with point_num_segments segments
        :param center: Absolute center position
        :param radius: Radius of the circle
        :param num_segments: Number of segments. Every second segment is drawn
        :param color: Drawing color
        :param draw_len: Number of segments to draw before leaving a gap
        :param gap_len: Number of segments left out by a gap
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        center_vec2: Vec2 = convert_coord(center, Vec2)

        if convert_global:
            center_vec2 = pv.global_vars.translate_screen_coord(center_vec2)
            radius = pv.global_vars.translate_scale(radius)
            thickness = pv.global_vars.translate_scale(thickness)

        outer: float = radius + thickness

        if offscreen_check and self._check_out_of_screen(
            (center_vec2.x - outer, center_vec2.y - outer), (outer * 2, outer * 2)
        ):
            return

        # If you want to know how tf this works. IDK myself. Ask AI
        all_indices = np.arange(num_segments, dtype=np.int32)

        mask = (all_indices % (draw_len + gap_len)) < draw_len
        active_indices = all_indices[mask].astype(np.float32)

        num_to_draw = active_indices.shape[0]
        if num_to_draw == 0:
            return

        step = m.tau / num_segments

        angles1 = active_indices * step
        angles2 = angles1 + step

        c1, s1 = np.cos(angles1), np.sin(angles1)
        c2, s2 = np.cos(angles2), np.sin(angles2)

        vertices = np.empty((num_to_draw, 4, 2), dtype=np.float32)

        vertices[:, 0, 0], vertices[:, 0, 1] = radius * c1, radius * s1
        vertices[:, 1, 0], vertices[:, 1, 1] = outer * c1, outer * s1

        vertices[:, 2, 0], vertices[:, 2, 1] = outer * c2, outer * s2
        vertices[:, 3, 0], vertices[:, 3, 1] = radius * c2, radius * s2

        glPushMatrix()
        glTranslate(center_vec2.x, center_vec2.y, 0.0)
        self.__set_color(color)

        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices)
        glDrawArrays(GL_QUADS, 0, num_to_draw * 4)
        glDisableClientState(GL_VERTEX_ARRAY)

        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(
                center_vec2, (radius * 2, radius * 2), centered=True
            )

    def draw_partial_dashed_circle(
        self,
        center: coord_t,
        radius: float,
        angle_start: coord_t,
        angle_end: coord_t,
        num_segments: int,
        color: Color | tColor,
        *,
        draw_len: int = 1,
        gap_len: int = 1,
        thickness: float = 1.0,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a partial dashed circle line with point_num_segments segments
        :param center: Absolute center position
        :param radius: Radius of the circle
        :param angle_start: Angle to start at as vector
        :param angle_end: Angle to end at as vector
        :param num_segments: Number of segments. Every second segment is drawn
        :param color: Drawing color
        :param draw_len: Number of segments to draw before leaving a gap
        :param gap_len: Number of segments left out by a gap
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        center_vec2: Vec2 = convert_coord(center, Vec2)
        start_vec: Vec2 = convert_coord(angle_start, Vec2)
        end_vec: Vec2 = convert_coord(angle_end, Vec2)

        if convert_global:
            center_vec2 = pv.global_vars.translate_screen_coord(center_vec2)
            radius = pv.global_vars.translate_scale(radius)
            thickness = pv.global_vars.translate_scale(thickness)

        outer = radius + thickness

        if offscreen_check and self._check_out_of_screen(
            (center_vec2.x - outer, center_vec2.y - outer), (outer * 2, outer * 2)
        ):
            return

        glPushMatrix()
        glTranslate(center_vec2.x, center_vec2.y, 0.0)

        self.__set_color(color)

        start_ang = start_vec.angle
        total_angle = normalize_angle(end_vec.angle - start_ang)

        step = total_angle / num_segments

        all_indices = np.arange(num_segments, dtype=np.int32)

        mask = (all_indices % (draw_len + gap_len)) < draw_len
        active_indices = all_indices[mask].astype(np.float32)

        num_to_draw = active_indices.shape[0]

        if num_to_draw == 0:
            glPopMatrix()
            return

        angles1 = start_ang + (active_indices * step)
        angles2 = angles1 + step

        c1 = np.cos(angles1)
        s1 = np.sin(angles1)
        c2 = np.cos(angles2)
        s2 = np.sin(angles2)

        vertices = np.empty((num_to_draw, 4, 2), dtype=np.float32)

        vertices[:, 0, 0] = radius * c1
        vertices[:, 0, 1] = radius * s1

        vertices[:, 1, 0] = outer * c1
        vertices[:, 1, 1] = outer * s1

        vertices[:, 2, 0] = outer * c2
        vertices[:, 2, 1] = outer * s2

        vertices[:, 3, 0] = radius * c2
        vertices[:, 3, 1] = radius * s2

        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, vertices)
        glDrawArrays(GL_QUADS, 0, num_to_draw * 4)
        glDisableClientState(GL_VERTEX_ARRAY)

        glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(
                center_vec2, (radius * 2, radius * 2), centered=True
            )

    # endregion

    # region Lines
    def draw_line(
        self,
        start: coord_t,
        end: coord_t,
        color: Color | tColor,
        *,
        global_position: bool = True,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a simple line
        :param start: Start position of the line
        :param end: End position of the line
        :param color: Drawing color
        :param global_position: IDK
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        start_vec2: Vec2 = convert_coord(start, Vec2)
        end_vec2: Vec2 = convert_coord(end, Vec2)

        if convert_global:
            start_vec2 = pv.global_vars.translate_screen_coord(start_vec2)
            end_vec2 = pv.global_vars.translate_screen_coord(end_vec2)

        # only draw if on screen
        if offscreen_check and self._check_out_of_screen(
            start_vec2, end_vec2 - start_vec2
        ):
            return

        if global_position:
            glPushMatrix()  # reset previous glTranslate statements

        self.__set_color(color)

        glBegin(GL_LINES)
        glVertex2f(start_vec2.x, start_vec2.y)
        glVertex2f(end_vec2.x, end_vec2.y)
        glEnd()

        if global_position:
            glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(start_vec2, end_vec2 - start_vec2)

    def draw_thick_line(
        self,
        start: coord_t,
        end: coord_t,
        color: Color | tColor,
        *,
        thickness: float = 1.0,
        global_position: bool = True,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a line with thickness
        :param start: Start position of the line
        :param end: End position of the line
        :param color: Drawing color
        :param thickness: Thickness of the line
        :param global_position: IDK
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        start_vec2: Vec2 = convert_coord(start, Vec2)
        end_vec2: Vec2 = convert_coord(end, Vec2)

        if convert_global:
            start_vec2 = pv.global_vars.translate_screen_coord(start_vec2)
            end_vec2 = pv.global_vars.translate_screen_coord(end_vec2)
            thickness = pv.global_vars.translate_scale(thickness)

        sx = start_vec2.x
        sy = start_vec2.y
        ex = end_vec2.x
        ey = end_vec2.y

        dx = ex - sx
        dy = ey - sy

        if offscreen_check and self._check_out_of_screen((sx, sy), (dx, dy)):
            return

        length = m.hypot(dx, dy)
        if length == 0.0:
            return

        self.__set_color(color)

        if global_position:
            glPushMatrix()

        half_thick = thickness * 0.5
        off_x = (-dy / length) * half_thick
        off_y = (dx / length) * half_thick

        glBegin(GL_QUADS)
        glVertex2f(sx + off_x, sy + off_y)
        glVertex2f(sx - off_x, sy - off_y)
        glVertex2f(ex - off_x, ey - off_y)
        glVertex2f(ex + off_x, ey + off_y)
        glEnd()

        if global_position:
            glPopMatrix()

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(start_vec2, end_vec2 - start_vec2)

    def draw_lines(
        self,
        points: Sequence[coord_t],
        color: Color | Sequence[Color],
        *,
        thickness: float = 1.0,
        global_position: bool = True,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a simple line
        :param points: list of line points
        :param color: one color or color for each point.

        :param thickness: line thickness
        :param global_position: position in global space or relative to previous
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        """
        if len(points) <= 1:
            return

        # convert points to Vec2
        points_: list[Vec2] = [convert_coord(c, Vec2) for c in points]  # type: ignore

        if convert_global:
            points_ = [pv.global_vars.translate_screen_coord(p) for p in points_]
            thickness = pv.global_vars.translate_scale(thickness)

        if offscreen_check:
            # check if all points are oob
            if self._check_out_of_screen(points_[0], (points_[0] - points_[1])):
                for point in points_:
                    if not self._check_out_of_screen(point, (1, 1)):
                        break

                else:
                    return

        # set color if only one is given or not enough are given
        color_list: bool = True
        if not isinstance(color, Sequence):
            self.__set_color(color)
            color_list = False

        elif isinstance(color, Sequence) and len(color) < len(points):
            self.__set_color(color[0])
            color = color[0]
            color_list = False

        # create local coordinate system
        if global_position:
            glPushMatrix()

        glBegin(GL_TRIANGLE_STRIP)

        # draw points as thick line
        n_points = len(points_)
        for i in range(n_points):
            if i == 0:
                direction = (points_[0] - points_[1]).normalize()

            elif i == n_points - 1:
                direction = (points_[-2] - points_[-1]).normalize()

            else:
                # use prev and next points as normal vector
                direction = (points_[i - 1] - points_[i + 1]).normalize()

            d = Vec2().from_polar(
                direction.angle + PI_2, thickness / 2
            )  # create 90° offset

            if color_list:
                self.__set_color(color[i])

            glVertex2f(*(points_[i] + d).xy)
            glVertex2f(*(points_[i] - d).xy)

        glEnd()

        if global_position:
            glPopMatrix()

    # endregion

    # region Texts and surfaces
    def draw_dynamic_text(
        self,
        pos: coord_t,
        text: str,
        *,
        color: Color | tColor = (255, 255, 255, 255),
        bg_color: Color | tColor = (0, 0, 0, 0),
        centered: bool = False,
        font_size: int = 64,
        font_family: str = "arial",
        bold: bool = False,
        italic: bool = False,
        line_height: float = 1.0,
        text_id: DynamicTextID | None = None,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> DynamicTextID:
        """
        Draw a text to the given position.

        :param pos: Position of the text
        :param text: Text to be drawn
        :param color: Text color
        :param bg_color: Background color
        :param centered: Whether pos is center or top left
        :param font_size: Size of the font
        :param font_family: Family of the font
        :param bold: Whether the text is bold
        :param italic: Whether the text is italic
        :param line_height: distance between lines
        :param text_id: NOT SUPPORTED
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        :return: DynamicTextID (None) - not implemented.
        """
        if not isinstance(bg_color, Color):
            bg_color = self.__set_color(bg_color)

        color_: Color = (
            self.__set_color(color) if not isinstance(color, Color) else color
        )

        pos: Vec2 = convert_coord(pos, Vec2)

        scale = 1.0
        if convert_global:
            pos = pv.global_vars.translate_screen_coord(pos)
            scale = pv.global_vars.translate_scale(1.0)

        font_key = (font_family, font_size, bold, italic)

        if font_key not in self.__dynamic_text_fonts:
            self.__dynamic_text_fonts[font_key] = GLFont(
                font_family, font_size, bold, italic
            )

        font = self.__dynamic_text_fonts[font_key]

        text_width, text_height = font.get_dimensions(text, scale)

        if centered:
            pos.x -= text_width / 2
            pos.y -= text_height / 2

        if offscreen_check and self._check_out_of_screen(
            (pos.x, pos.y), (text_width, text_height)
        ):
            return -1

        if bg_color.a255 > 0:
            self.draw_rect(
                pos.xy,
                (text_width, text_height),
                bg_color,
                convert_global=convert_global,
            )

        font.draw(text, pos.x, pos.y, color_, scale=scale, line_height=line_height)

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds(pos, (text_width, text_height))

        return 0

    def get_dynamic_text_size(
        self,
        text: str,
        *,
        font_size: int = 64,
        font_family: str = "arial",
        bold: bool = False,
        italic: bool = False,
        line_height: float = 1.0,
        convert_global: bool = True,
    ) -> tuple[float, float]:
        """
        Get size of dynamic text.

        :param text: Text to be drawn
        :param font_size: Size of the font
        :param font_family: Family of the font
        :param bold: Whether the text is bold
        :param italic: Whether the text is italic
        :param line_height: distance between lines
        :param convert_global: Whether to apply the global game scaling to pos and size
        :return: size of text
        """
        scale = 1.0
        if convert_global:
            scale = pv.global_vars.translate_scale(1.0)

        font_key = (font_family, font_size, bold, italic)

        if font_key not in self.__dynamic_text_fonts:
            self.__dynamic_text_fonts[font_key] = GLFont(
                font_family, font_size, bold, italic
            )

        font = self.__dynamic_text_fonts[font_key]

        return font.get_dimensions(text, scale, line_height)

    def generate_static_text(
        self,
        text: str,
        color: Color | tColor,
        bg_color: Color | tColor | None = None,
        *,
        font_size: int = 64,
        font_family: str = "arial",
        bold: bool = False,
        italic: bool = False,
    ) -> StaticTextID:
        """
        Generate a static text
        :param text: Text to be drawn
        :param color: Text color
        :param bg_color: Background color
        :param font_size: Font size
        :param font_family: Font family
        :param bold: Whether the text is bold
        :param italic: Whether the text is italic
        :return: StaticTextID integer.
        """
        surface = self.get_font(font_size, font_family, bold, italic).render(
            text, True, convert_color(color, Color).rgba255
        )
        w, h = surface.get_size()

        text_data = pg.image.tobytes(surface, "RGBA", False)

        tex_id = glGenTextures(1)

        current_id = self.__static_text_id_counter

        self.__static_text_graphics[current_id] = (tex_id, (w, h))

        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, text_data
        )

        self.__static_text_id_counter += 1

        return current_id

    def draw_static_text(
        self,
        pos: coord_t,
        text_id: StaticTextID,
        *,
        centered: bool = False,
        scale: float = 1.0,
        convert_global: bool = True,
        offscreen_check: bool = True,
    ) -> None:
        """
        Draw a surface
        :param pos: Position of the surface
        :param text_id: Text to draw, generated by generate_static_text()
        :param centered: Whether pos is center or top left
        :param scale: Scale the surface size
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing.
        """
        tex_id = self.__static_text_graphics[text_id][0]
        w, h = self.__static_text_graphics[text_id][1]
        pos: Vec2 = convert_coord(pos, Vec2)

        if convert_global:
            pos = pv.global_vars.translate_screen_coord(pos)
            scale = pv.global_vars.translate_scale(scale)

        scaled_w = w * scale
        scaled_h = h * scale

        px = pos.x
        py = pos.y

        if centered:
            px -= scaled_w * 0.5
            py -= scaled_h * 0.5

        if self._check_out_of_screen((px, py), (scaled_w, scaled_h)):
            return

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glBindTexture(GL_TEXTURE_2D, tex_id)

        glPushMatrix()
        glTranslatef(px, py, 0.0)
        glColor4f(1.0, 1.0, 1.0, 1.0)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(0.0, 0.0)

        glTexCoord2f(0.0, 1.0)
        glVertex2f(0.0, scaled_h)

        glTexCoord2f(1.0, 1.0)
        glVertex2f(scaled_w, scaled_h)

        glTexCoord2f(1.0, 0.0)
        glVertex2f(scaled_w, 0.0)
        glEnd()

        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

        if OpenGLRenderer.DRAW_DEBUG_BOUNDS:
            self._draw_debug_bounds((px, py), (scaled_w, scaled_h))

    # endregion
