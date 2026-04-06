"""
_base_renderer.py
21. March 2024

prototype renderer

Author:
Nilusink
"""
from PIL import Image
import pygame as pg
import typing as tp
from types import EllipsisType
import abc

from ..logic import Color, coord_t, Vec2

# define types
type Color3 = tuple[float, float, float]
type Color4 = tuple[float, float, float, float]
type tColor = Color3 | Color4

# depending on the renderer, TextureID will be a different type
type TextureID = tp.Any
type TextID = tp.Any


class BaseRenderer(abc.ABC):
    """
    Abstract Renderer Class
    """

    @abc.abstractmethod
    def init(self, title: str) -> None:
        """
        initialize the renderer and global_vars
        :param title: Window title
        """
        raise NotImplementedError

    @abc.abstractmethod
    def load_texture(
            self,
            image: Image.Image,
            size: coord_t | None = None,
            mirror: tp.Literal["x", "y", "xy", "yx", ""] = "",
    ) -> tuple[TextureID, tuple[int, int]]:
        """
        Load an image texture (saves it internally)
        :param image: Image to load
        :param size: Size of image or None
        :param mirror: Axes to mirror the image on
        :returns: texture_id, (width, height)
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_textured_quad(
            self,
            texture_id: TextureID,
            pos: coord_t,
            size: coord_t,
            convert_global: bool = True,
            rotate_angle: float = 0,
            rotate_anchor: Vec2 | tuple[float, float] | EllipsisType = ...,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a rectangle with a texture
        :param texture_id: ID of the texture to draw
        :param pos: Absolute position on window
        :param size: Absolute size on window
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param rotate_angle: Angle in degrees to rotate the image at
        :param rotate_anchor: At what pixel to rotate at
        :param offscreen_check: Whether to check it the element is on the window before drawing
        """
        raise NotImplementedError

    # region Stencil
    @abc.abstractmethod
    def apply_stencil[**A](
            self,
            stencil_func: tp.Callable[A, tp.Any],
            show_stencil: bool = False,
            *args: A.args,
            **kwargs: A.kwargs
    ) -> None: ...

    @abc.abstractmethod
    def start_stencil(self, show_stencil: bool = False) -> None: ...

    @abc.abstractmethod
    def enable_stencil(self, show_stencil: bool = False) -> None: ...

    @abc.abstractmethod
    def disable_stencil(self) -> None: ...

    # endregion

    @abc.abstractmethod
    def check_out_of_screen(
            self,
            pos,
            size,
    ) -> bool:
        """
        check if a rect is out of screen
        """
        raise NotImplementedError

    # region Drawing
    @abc.abstractmethod
    def draw_polygon(
            self,
            vertices: tp.Iterable[coord_t],
            color: Color | tColor,
            center: coord_t = None,
            convert_global: bool = True
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def draw_circle(
            self,
            center: coord_t,
            radius: float,
            num_segments: int,
            color: Color | tColor,
            convert_global: bool = True
    ) -> None:
        """
        draw a circle
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_line_circle(
            self,
            center: coord_t,
            radius: float,
            num_segments: int,
            color: Color | tColor,
            thickness: float = 1,
            convert_global: bool = True
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def draw_partial_circle(
            self,
            center: coord_t,
            radius: float,
            angle_start: coord_t,
            angle_end: coord_t,
            num_segments: int,
            color: Color | tColor,
            convert_global=True
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def draw_rect(
            self,
            start: coord_t,
            size: coord_t,
            color: Color | tColor,
            convert_global: bool = True
    ) -> None:
        """
        draw a rectangle
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_dashed_circle(
            self,
            center: coord_t,
            radius: float,
            num_segments: int,
            color: Color | tColor,
            thickness: int = 1,
            convert_global: bool = True
    ) -> None:
        """
        draw a dashed circle with num_segments segments
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_partial_dashed_circle(
            self,
            center: coord_t,
            radius: float,
            angle_start: coord_t,
            angle_end: coord_t,
            num_segments: int,
            color: Color | tColor,
            thickness=1,
            convert_global=True
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def draw_line(
            self,
            start: coord_t,
            end: coord_t,
            color: Color | tColor,
            global_position: bool = True,
            convert_global: bool = True
    ) -> None:
        """
        draw a simple line
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_thick_line(
            self,
            start: coord_t,
            end: coord_t,
            color: Color | tColor,
            thickness: float = 1.0,
            global_position: bool = True,
            convert_global: bool = True
    ) -> None:
        """
        draw a line with thickness using a quad
        """

    @abc.abstractmethod
    def draw_rounded_rect(
            self,
            start: coord_t,
            size: coord_t,
            color: Color | tColor,
            radius: float,
            convert_global: bool = True
            # radius_top_left: float = ...,
            # radius_top_right: float = ...,
            # radius_bottom_left: float = ...,
            # radius_bottom_right: float = ...
    ) -> None:
        """
        draw a rect with rounded corners
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_text(
            self,
            pos: coord_t,
            text: str,
            color: Color | tColor = (255, 255, 255, 255),
            bg_color: Color | tColor = (0, 0, 0, 0),
            centered: bool = False,
            font_size: int = 64,
            font_family: str = "arial",
            bold: bool = False,
            italic: bool = False,
            convert_global: bool = True
    ) -> tuple[int, int]:
        """
        draw a text to the given position

        :returns: the size of the drawn text
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_pg_surf(
            self,
            pos: coord_t,
            surface: pg.Surface,
            centered: bool = False,
            convert_global: bool = True
    ) -> None:
        """
        draw a pygame surface
        """
        raise NotImplementedError

    @abc.abstractmethod
    def generate_pg_surf_text(
            self,
            text: str,
            color: Color | tColor,
            bg_color: Color | tColor,
            font_size: int = 64,
            font_family: str = "arial",
            bold: bool = False,
            italic: bool = False,
            convert_global: bool = True
    ) -> pg.Surface:
        """
        generates a pygame surface from a text
        """
        raise NotImplementedError

    # endregion
