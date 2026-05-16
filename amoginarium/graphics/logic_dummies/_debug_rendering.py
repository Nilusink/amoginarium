"""
amoginarium/graphics/logic_dummies/_dynamic_debug_rendering.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium import pv
from amoginarium.shared import CIDType, GraphicsCIDs
from amoginarium.shared.utility import MASK16, Vec2

from ..entities import Drawn_0, Drawn_2
from ..render_bindings import renderer
from ._synced_entities import SyncedGraphicsEntity


class DebugRectangleEntity(SyncedGraphicsEntity):
    """A graphics-side entity used to render debug rectangles and their corner points"""

    __slots__ = (
        "__point_color",
        "__point_radius",
        "__point_num_segments",
        "__outline_color",
        "__outline_thickness",
        "__fill_color",
        "__centered",
        "__convert_global",
    )

    # region ClassVars
    _CID: tp.ClassVar[CIDType] = GraphicsCIDs.debug_rectangle
    # endregion
    # region InstanceVars
    __point_color: tuple[int, int, int] | tuple[int, int, int, int]
    __point_radius: int
    __point_num_segments: int
    __outline_color: tuple[int, int, int] | tuple[int, int, int, int]
    __outline_thickness: int
    __fill_color: tuple[int, int, int] | tuple[int, int, int, int]
    __centered: bool
    __convert_global: bool  # endregion

    def __init__(
        self,
        sync_id: int,
        point_color: tuple[int, int, int] | tuple[int, int, int, int],
        point_radius: int,
        point_num_segments: int,
        outline_color: tuple[int, int, int] | tuple[int, int, int, int],
        outline_thickness: int,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int],
        centered: bool,
        convert_global: bool,
        **_kwargs: tp.Any,
    ) -> None:
        """
        Initializes a DebugRectangleEntity.
        :param sync_id: The unique synchronization ID for the entity.
        :param point_color: RGBA or RGB tuple for the corner points.
        :param point_radius: Radius of the corner points in pixels.
        :param point_num_segments: Number of segments for circle rendering.
        :param outline_color: RGBA or RGB tuple for the rectangle outline.
        :param outline_thickness: Thickness of the outline in pixels.
        :param fill_color: RGBA or RGB tuple for the rectangle fill.
        :param centered: Whether the position represents the center or top-left.
        :param convert_global: Whether to convert coordinates to global screen space.
        """
        super().__init__(sync_id)
        self.__point_color = point_color
        self.__point_radius = point_radius
        self.__point_num_segments = point_num_segments
        self.__outline_color = outline_color
        self.__outline_thickness = outline_thickness
        self.__fill_color = fill_color
        self.__centered = centered
        self.__convert_global = convert_global

        self.add(Drawn_2)
        self.remove(Drawn_0)

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        """
        Renders the debug rectangle and its corner points using the current state.
        :param delta_cal: The time delta for interpolation (unused here).
        :param layer: The rendering layer index.
        """
        pos = (
            self.world_position - self.size / 2
            if self.__centered
            else self.world_position
        )
        size = self.size

        # Fill
        renderer.draw_rect(
            start=pos,
            size=size,
            color=self.__fill_color,
            convert_global=self.__convert_global,
        )

        # Draw outline
        if self.__outline_thickness > 0:
            renderer.draw_rect_line(
                start=pos,
                size=size,
                color=self.__outline_color,
                thickness=self.__outline_thickness,
                convert_global=self.__convert_global,
            )

        # Draw circles
        if self.__point_radius > 0:
            circle_pos: tuple[int, int]
            for circle_pos in (
                pos.xy,
                (pos.x + size.x, pos.y),
                (pos.x + size.x, pos.y + size.y),
                (pos.x, pos.y + size.y),
            ):
                renderer.draw_circle(
                    center=circle_pos,
                    radius=self.__point_radius,
                    num_segments=self.__point_num_segments,
                    color=self.__point_color,
                    convert_global=self.__convert_global,
                )


class DebugPolygonEntity(SyncedGraphicsEntity):
    """A graphics-side entity used to render debug polygons with up to 8 vertices."""

    __slots__ = (
        "__p1",
        "__p2",
        "__p3",
        "__p4",
        "__p5",
        "__p6",
        "__p7",
        "__p8",
        "__point_color",
        "__point_radius",
        "__point_num_segments",
        "__outline_color",
        "__outline_thickness",
        "__fill_color",
        "__convert_global",
    )

    # region ClassVars
    _CID: tp.ClassVar[CIDType] = GraphicsCIDs.debug_polygon
    # endregion
    # region InstanceVars
    __p1: Vec2
    __p2: Vec2
    __p3: Vec2
    __p4: Vec2
    __p5: Vec2
    __p6: Vec2
    __p7: Vec2
    __p8: Vec2
    __point_color: tuple[int, int, int] | tuple[int, int, int, int]
    __point_radius: int
    __point_num_segments: int
    __outline_color: tuple[int, int, int] | tuple[int, int, int, int]
    __outline_thickness: int
    __fill_color: tuple[int, int, int] | tuple[int, int, int, int]
    __convert_global: bool  # endregion

    def __init__(
        self,
        sync_id: int,
        point_color: tuple[int, int, int] | tuple[int, int, int, int],
        point_radius: int,
        point_num_segments: int,
        outline_color: tuple[int, int, int] | tuple[int, int, int, int],
        outline_thickness: int,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int],
        convert_global: bool,
        **_kwargs: tp.Any,
    ) -> None:
        """
        Initializes a DebugPolygonEntity.
        :param sync_id: The unique synchronization ID for the entity.
        :param point_color: RGBA or RGB tuple for the vertex points.
        :param point_radius: Radius of the vertex points.
        :param point_num_segments: Segments for circle rendering.
        :param outline_color: RGBA or RGB tuple for the polygon outline.
        :param outline_thickness: Thickness of the outline.
        :param fill_color: RGBA or RGB tuple for the polygon fill.
        :param convert_global: Whether to convert coordinates to global screen space.
        """
        self.__p1 = Vec2()
        self.__p2 = Vec2()
        self.__p3 = Vec2()
        self.__p4 = Vec2()
        self.__p5 = Vec2()
        self.__p6 = Vec2()
        self.__p7 = Vec2()
        self.__p8 = Vec2()

        self.__point_color = point_color
        self.__point_radius = point_radius
        self.__point_num_segments = point_num_segments
        self.__outline_color = outline_color
        self.__outline_thickness = outline_thickness
        self.__fill_color = fill_color
        self.__convert_global = convert_global

        super().__init__(sync_id)

        self.add(Drawn_2)
        self.remove(Drawn_0)

    def _update_from_buffer(self) -> None:
        self.alive = self._get_bit("flags", 0)
        self._logic_visibility = self._get_bit("flags", 1)
        self._highlight = self._get_bit("flags", 2)

        # normal positions
        self.__p1.x = self._buff.pos_x
        self.__p1.y = self._buff.pos_y

        self.__p2.length = self._buff.size_y
        self.__p2.angle = float(self._buff.size_x) / 10_000

        # float points
        self.__p3.length = self._buff.param3 & MASK16
        self.__p4.length = (self._buff.param3 >> 16) & MASK16
        self.__p5.length = (self._buff.param3 >> 32) & MASK16
        self.__p6.length = (self._buff.param3 >> 48) & MASK16

        self.__p3.angle = self._buff.param0
        self.__p4.angle = self._buff.param1
        self.__p5.angle = self._buff.param2
        self.__p6.angle = float(self._buff.facing) / 10_000

        # dual-packed variables
        self.__p7.length = (self._buff.param4 >> 16) & MASK16
        self.__p7.angle = float(self._buff.param4 & MASK16) / 10_000
        self.__p8.length = (self._buff.param4 >> 48) & MASK16
        self.__p8.angle = float((self._buff.param4 >> 32) & MASK16) / 10_000

    # noinspection DuplicatedCode
    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        """
        Renders the debug polygon (Fill, Outline, Points).
        :param delta_cal: The time delta for interpolation.
        :param layer: The rendering layer index.
        """
        # Filter active points (non-zero)
        world_pos = pv.global_vars.get_world_position()

        points: list[Vec2] = [
            p - world_pos
            for p in (
                self.__p1,
                self.__p2,
                self.__p3,
                self.__p4,
                self.__p5,
                self.__p6,
                self.__p7,
                self.__p8,
            )
            if p.x != 0 or p.y != 0
        ]

        if not points:
            return

        self.__convert_global = True
        # 1. Fill
        renderer.draw_polygon(
            vertices=points,
            color=self.__fill_color,
            convert_global=self.__convert_global,
        )

        # 2. Outline
        if self.__outline_thickness > 0:
            renderer.draw_polygon_line(
                vertices=points,
                color=self.__outline_color,
                thickness=self.__outline_thickness,
                convert_global=self.__convert_global,
            )

        # 3. Points
        if self.__point_radius > 0:
            for point in points:
                renderer.draw_circle(
                    center=point,
                    radius=self.__point_radius,
                    num_segments=self.__point_num_segments,
                    color=self.__point_color,
                    convert_global=self.__convert_global,
                )


class DebugCircleEntity(SyncedGraphicsEntity):
    """A graphics-side entity used to render debug circles and their center points"""

    __slots__ = (
        "__point_color",
        "__point_radius",
        "__point_num_segments",
        "__outline_color",
        "__outline_thickness",
        "__fill_color",
        "__centered",
        "__convert_global",
    )

    # region ClassVars
    _CID: tp.ClassVar[CIDType] = GraphicsCIDs.debug_circle
    # endregion
    # region InstanceVars
    __point_color: tuple[int, int, int] | tuple[int, int, int, int]
    __point_radius: int
    __point_num_segments: int
    __outline_color: tuple[int, int, int] | tuple[int, int, int, int]
    __outline_thickness: int
    __fill_color: tuple[int, int, int] | tuple[int, int, int, int]
    __centered: bool
    __convert_global: bool  # endregion

    def __init__(
        self,
        sync_id: int,
        point_color: tuple[int, int, int] | tuple[int, int, int, int],
        point_radius: int,
        point_num_segments: int,
        outline_color: tuple[int, int, int] | tuple[int, int, int, int],
        outline_thickness: int,
        fill_color: tuple[int, int, int] | tuple[int, int, int, int],
        centered: bool,
        convert_global: bool,
        **_kwargs: tp.Any,
    ) -> None:
        """
        Initializes a DebugCircleEntity.
        :param sync_id: The unique synchronization ID for the entity.
        :param point_color: RGBA or RGB tuple for the center point.
        :param point_radius: Radius of the center point in pixels.
        :param point_num_segments: Number of segments for circle rendering.
        :param outline_color: RGBA or RGB tuple for the circle outline.
        :param outline_thickness: Thickness of the outline in pixels.
        :param fill_color: RGBA or RGB tuple for the circle fill.
        :param centered: Whether the position represents the center or top-left.
        :param convert_global: Whether to convert coordinates to global screen space.
        """
        super().__init__(sync_id)
        self.__point_color = point_color
        self.__point_radius = point_radius
        self.__point_num_segments = point_num_segments
        self.__outline_color = outline_color
        self.__outline_thickness = outline_thickness
        self.__fill_color = fill_color
        self.__centered = centered
        self.__convert_global = convert_global

        self.add(Drawn_2)
        self.remove(Drawn_0)

    def _gl_draw(self, delta_cal: float, layer: int = 0) -> None:
        """
        Renders the debug circle and its center point.
        :param delta_cal: The time delta for interpolation (unused here).
        :param layer: The rendering layer index.
        """
        radius = self.size.x
        center = (
            self.world_position
            if self.__centered
            else self.world_position + Vec2(radius, radius)
        )

        renderer.draw_circle(
            center=center,
            radius=radius,
            num_segments=self.__point_num_segments,
            color=self.__fill_color,
            convert_global=self.__convert_global,
        )

        # Outline
        if self.__outline_thickness > 0:
            renderer.draw_line_circle(
                center=center,
                radius=radius,
                num_segments=self.__point_num_segments,
                color=self.__outline_color,
                thickness=self.__outline_thickness,
                convert_global=self.__convert_global,
            )

        # Center Point
        if self.__point_radius > 0:
            renderer.draw_circle(
                center=center,
                radius=self.__point_radius,
                num_segments=self.__point_num_segments,
                color=self.__point_color,
                convert_global=self.__convert_global,
            )
