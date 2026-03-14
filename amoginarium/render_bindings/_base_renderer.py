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

from ..logic import Color, coord_t


# define types
type Color3 = tuple[float, float, float]
type Color4 = tuple[float, float, float, float]
type tColor = Color3 | Color4

# depending on the renderer, TextureID will be a different type
type TextureID = tp.Any


class BaseRenderer:
    def init(self, title: str) -> None:
        """
        initialize the renderer and global_vars
        """
        raise NotImplementedError

    @staticmethod
    def load_texture(
            image: Image.Image,
            size: coord_t | None = None,
            mirror: tp.Literal["x", "y", "xy", "yx"] = "",
    ) -> tuple[TextureID, tuple[int, int]]:
        """
        load an image texture

        :returns: texture_id, (width, height)
        """
        raise NotImplementedError

    @staticmethod
    def draw_textured_quad(
            texture_id: TextureID,
            pos: coord_t,
            size: coord_t,
            convert_global: bool = True,
            rotate_angle: float = 0,
            rotate_anchor: coord_t = ...
    ) -> None:
        """
        draw a rectangle with a texture
        """
        raise NotImplementedError

    def apply_stencil[**A](
            self,
            stencil_func: tp.Callable[[A], tp.Any],
            show_stencil: bool = False,
            *args: A.args,
            **kwargs: A.kwargs
    ) -> None: ...

    def disable_stencil(self) -> None: ...

    def draw_polygon(
            self,
            vertices: tp.Iterable[coord_t],
            color: Color | tColor,
            center: coord_t = None,
            convert_global: bool = True
    ) -> None:
        raise NotImplementedError

    @staticmethod
    def check_out_of_screen(
            pos,
            size,
    ) -> bool:
        """
        check if a rect is out of screen
        """
        raise NotImplementedError

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

    def draw_rounded_rect(
            self,
            start: coord_t,
            size: coord_t,
            color: Color | tColor,
            radius: float,
            # radius_top_left: float = ...,
            # radius_top_right: float = ...,
            # radius_bottom_left: float = ...,
            # radius_bottom_right: float = ...
    ) -> None:
        """
        draw a rect with rounded corners
        """
        raise NotImplementedError

    def draw_text(
            self,
            pos: coord_t,
            text: str,
            color: Color | tColor,
            bg_color: Color | tColor,
            centered: bool = False,
            font_size: int = 64,
            font_family: str = "arial",
            bold: bool = False,
            italic: bool = False
    ) -> tuple[int, int]:
        """
        draw a text to the given position

        :returns: the size of the drawn text
        """
        raise NotImplementedError

    def draw_pg_surf(
            self,
            pos: coord_t,
            surface: pg.Surface,
            centered: bool = False
    ) -> None:
        """
        draw a pygame surface
        """
        raise NotImplementedError

    def generate_pg_surf_text(
            self,
            text: str,
            color: Color | tColor,
            bg_color: Color | tColor,
            font_size: int = 64,
            font_family: str = "arial",
            bold: bool = False,
            italic: bool = False
    ) -> pg.Surface:
        """
        generates a pygame surface from a text
        """
        raise NotImplementedError
