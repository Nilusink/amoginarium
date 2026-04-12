"""
_base_renderer.py
21. March 2024

prototype renderer

Author:
Nilusink, LukasKrah
"""

from types import EllipsisType
from PIL import Image
import typing as tp
import abc

from amoginarium.shared.utility import Color, coord_t

# define types
type Color3 = tuple[float, float, float]
type Color4 = tuple[float, float, float, float]
type tColor = Color3 | Color4

# depending on the renderer, TextureID will be a different type



class BaseRenderer(abc.ABC):
    """
    Abstract Renderer Class
    """
    type TextureID = tp.Any
    type StaticTextID = tp.Any
    type DynamicTextID = tp.Any

    # region Init and Loading
    @abc.abstractmethod
    def init(self, title: str) -> None:
        """
        Initialize the renderer and pv.global_vars
        :param title: Window title
        :raises NotImplementedError: If the renderer does not implement this method
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
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    # endregion

    # region Stencil
    # todo mytodo - stencils work!
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

    # region Textured
    @abc.abstractmethod
    def draw_textured_quad(
            self,
            texture_id: TextureID,
            pos: coord_t,
            size: coord_t,
            convert_global: bool = True,
            rotate_angle: float = 0,
            rotate_anchor: coord_t | EllipsisType = ...,
            pixel_perfect: bool = False,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a rectangle with a texture
        :param texture_id: ID of the texture to draw
        :param pos: Absolute position on window
        :param size: Absolute size on window
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param rotate_angle: Angle in degrees to rotate the image at
        :param rotate_anchor: At what pixel to rotate at. Defaults to center position
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :param pixel_perfect: Whether to draw pixel perfect
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    # endregion

    # region Basic shapes
    @abc.abstractmethod
    def draw_polygon(
            self,
            vertices: tp.Iterable[coord_t],
            color: Color | tColor,
            center: coord_t = None,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a polygon with fill
        :param vertices: Coord of the corner points of the polygon
        :param color: Drawing color
        :param center: Optional center position
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_rect(
            self,
            start: coord_t,
            size: coord_t,
            color: Color | tColor,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a rectangle with fill
        :param start: Absolute top left corner position
        :param size: Width and height of the rectangle
        :param color: Drawing color
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_rounded_rect(
            self,
            start: coord_t,
            size: coord_t,
            color: Color | tColor,
            radius: float,
            top_left_radius: float | None = None,
            top_right_radius: float | None = None,
            bottom_left_radius: float | None = None,
            bottom_right_radius: float | None = None,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a rect with rounded corners with fill
        :param start: Absolute top left corner position
        :param size: Width and height of the rectangle
        :param color: Drawing color
        :param radius: Radius of the corners
        :param top_left_radius: Individual radius for the top left corner. Defaults to radius
        :param top_right_radius: Individual radius for the top right corner. Defaults to radius
        :param bottom_left_radius: Individual radius for the bottom left corner. Defaults to radius
        :param bottom_right_radius: Individual radius for the bottom right corner. Defaults to radius
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_rect_line(
            self,
            start: coord_t,
            size: coord_t,
            color: Color | tColor,
            thickness: float = 1.0,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a rectangle outline without fill
        :param start: Absolute top left corner position
        :param size: Width and height of the rectangle
        :param color: Drawing color
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_rounded_rect_line(
            self,
            start: coord_t,
            size: coord_t,
            color: Color | tColor,
            radius: float,
            top_left_radius: float | None = None,
            top_right_radius: float | None = None,
            bottom_left_radius: float | None = None,
            bottom_right_radius: float | None = None,
            thickness: float = 1.0,
            convert_global: bool = True,
            offscreen_check: bool = True
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
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_bar(
            self,
            pos: coord_t,
            size: coord_t,
            colors: tuple[Color, Color, Color] | tuple[Color, Color] | tuple[Color],
            progress: float,
            *,
            background_color: Color | EllipsisType = ...,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        # todo: MYTODO - comment
        :param pos:
        :param size:
        :param colors:
        :param progress:
        :param background_color:
        :param convert_global:
        :param offscreen_check:
        """
        raise NotImplementedError

    # endregion

    # region Circles
    @abc.abstractmethod
    def draw_circle(
            self,
            center: coord_t,
            radius: float,
            num_segments: int,
            color: Color | tColor,
            *,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a circle with fill
        :param center: Absolute center position
        :param radius: Radius of the circle
        :param num_segments: Number of segments
        :param color: Drawing color
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_line_circle(
            self,
            center: coord_t,
            radius: float,
            num_segments: int,
            color: Color | tColor,
            *,
            thickness: float = 1.0,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a circle outline
        :param center: Absolute center position
        :param radius: Radius of the circle
        :param num_segments: Number of segments
        :param color: Drawing color
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
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
            *,
            convert_global=True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a partial circle with fill
        :param center: Absolute center position
        :param radius: Radius of the circle
        :param angle_start: Angle to start at as vector
        :param angle_end: Angle to end at as vector
        :param num_segments: Number of segments
        :param color: Drawing color
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
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
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a dashed circle line with num_segments segments
        :param center: Absolute center position
        :param radius: Radius of the circle
        :param num_segments: Number of segments. Every second segment is drawn
        :param color: Drawing color
        :param draw_len: Number of segments to draw before leaving a gap
        :param gap_len: Number of segments left out by a gap
        :param thickness: Thickness of the outline
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
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
            *,
            draw_len: int = 1,
            gap_len: int = 1,
            thickness=1,
            convert_global=True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a partial dashed circle line with num_segments segments
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
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    # endregion

    # region Lines
    @abc.abstractmethod
    def draw_line(
            self,
            start: coord_t,
            end: coord_t,
            color: Color | tColor,
            *,
            global_position: bool = True,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a simple line
        :param start: Start position of the line
        :param end: End position of the line
        :param color: Drawing color
        :param global_position: IDK
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_thick_line(
            self,
            start: coord_t,
            end: coord_t,
            color: Color | tColor,
            *,
            thickness: float = 1.0,
            global_position: bool = True,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a line with thickness
        :param start: Start position of the line
        :param end: End position of the line
        :param color: Drawing color
        :param thickness: Thickness of the line
        :param global_position: IDK
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """

    # endregion

    # region Texts and surfaces
    @abc.abstractmethod
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
            text_id: DynamicTextID | None = None,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> DynamicTextID:
        """
        Draw a dynamic text to the given position
        :param pos: Position of the text
        :param text: Text to be drawn
        :param color: Text color
        :param bg_color: Background color
        :param centered: Whether pos is center or top left
        :param font_size: Size of the font
        :param font_family: Family of the font
        :param bold: Whether the text is bold
        :param italic: Whether the text is italic
        :param text_id: Optional ID of the old dynamic text. A renderer can use this to optimize the dynamic text drawing
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :return: DynamicTextID
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
    def draw_static_text(
            self,
            pos: coord_t,
            text_id: StaticTextID,
            *,
            centered: bool = False,
            scale: float = 1.0,
            convert_global: bool = True,
            offscreen_check: bool = True
    ) -> None:
        """
        Draw a static text
        :param pos: Position of the text
        :param text_id: Text to draw, generated by generate_static_text()
        :param centered: Whether pos is center or top left
        :param scale: Scale the text size
        :param convert_global: Whether to apply the global game scaling to pos and size
        :param offscreen_check: Whether to check it the element is on the window before drawing
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError

    @abc.abstractmethod
    def generate_static_text(
            self,
            text: str,
            color: Color | tColor,
            bg_color: Color | tColor,
            *,
            font_size: int = 64,
            font_family: str = "arial",
            bold: bool = False,
            italic: bool = False
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
        :return: StaticTextID
        :raises NotImplementedError: If the renderer does not implement this method
        """
        raise NotImplementedError
    # endregion
