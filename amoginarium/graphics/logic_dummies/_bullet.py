"""
Bullet dummy entity.

Path: amoginarium/graphics/logic_dummies/_bullet.py
Project: amoginarium
Created: 31.03.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

from types import EllipsisType
from typing import TYPE_CHECKING

from amoginarium import pv
from amoginarium.shared import DummyCIDs
from amoginarium.shared.utility import Color, convert_color, convert_coord
from amoginarium.shared.utility import fade, get_default, Vec2

from ..entities import explosion
from ..render_bindings import renderer
from ..textures import textures
from ._synced_entities import SyncedImageEntity

if TYPE_CHECKING:
    from amoginarium.shared.utility import coord_t

    from ._synced_entities import BaseGraphicsEntity

BULLET_PATH = "bullet"


class BulletDummy(SyncedImageEntity):
    """
    ``param0`` explosion size
    ``param1`` velocity (length)
    ``param2`` velocity (angle).
    """

    __slots__ = [
        "_spawn_time",
        "_visibility_offset",
        "_last_pos",
        "_target_pos",
        "_trace",
        "_c_trace_color",
        "_show_trace",
        "_current_trace_length",
        "_max_trace_length",
        "_fade_trace",
        "_original_alpha",
        "_trace_len",
        "_trace_only",
        "_kill_next",
    ]

    _CID = DummyCIDs.base_bullet
    _default_size: Vec2 = Vec2().from_cartesian(64, 64)
    _image_name: str = BULLET_PATH
    _image_mirror: str = ""
    _trace_color: Color | tuple[Color, Color] = Color().from_255(255, 255, 60)
    _trace_length: float = 100  # length in coords
    _trace_fade_color_time: float = 1.5  # only applies if two colors are specified
    _trace_show: bool = True
    _trace_fade: bool = True
    _trace_width_mult: float = 1

    _kill_next: int | None

    _bullet_image: int | EllipsisType = ...

    @classmethod
    def load_textures(cls) -> None:
        """Load all required textures ONCE per class."""
        if cls.__dict__.get("_bullet_image", ...) is ...:
            if isinstance(cls._default_size, (int, float)):
                cls._default_size = Vec2().from_cartesian(
                    cls._default_size, cls._default_size
                )

            cls._bullet_image, _ = textures.get_texture(
                cls._image_name,
                cls._default_size,
                cls._image_mirror,
                pixel_perfect=True,
            )

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # make sure subclasses initialize their own bullet textures
        cls._bullet_image = ...

    def __init__(
        self,
        sync_id: int,
        spawn_time: float,
        position: coord_t,
        size: int | Vec2 | EllipsisType = ...,
        parent: BaseGraphicsEntity | None = None,
        visibility_offset: float = 0,
        target_pos: Vec2 | EllipsisType = ...,
        show_trace: bool | EllipsisType = ...,
        trace_color: Color | tuple[Color, Color] | EllipsisType = ...,
        trace_length: float | EllipsisType = ...,
        fade_trace: bool | EllipsisType = ...,
    ) -> None:
        size = get_default(size, self._default_size)

        if not isinstance(size, Vec2):
            size: Vec2 = Vec2().from_cartesian(size, size)  # type: ignore

        self._trace_only = False
        self._trace_len = 1
        self._spawn_time = spawn_time
        self._visibility_offset = visibility_offset
        self._last_pos: Vec2 = Vec2().from_cartesian(*convert_coord(position, Vec2).xy)
        self.pos = self._last_pos.copy()
        self._trace = []
        self._current_trace_length = 0
        self._max_trace_length = (
            trace_length if trace_length is not ... else self._trace_length
        )
        self._fade_trace = fade_trace if trace_length is not ... else self._trace_fade
        self._show_trace = show_trace if show_trace is not ... else self._trace_show

        self._kill_next = None

        if not isinstance(target_pos, EllipsisType):
            self._target_pos = convert_coord(target_pos, Vec2)

        else:
            self._target_pos = ...

        self._c_trace_color: Color | tuple[Color, Color]
        if not isinstance(trace_color, EllipsisType):
            if isinstance(trace_color, (tuple, list)):
                self._c_trace_color: tuple[Color, Color] = (
                    convert_color(c, Color) for c in trace_color
                )

            else:
                self._c_trace_color: Color = convert_color(trace_color, Color)
                self._original_alpha = self._c_trace_color.a1

        elif isinstance(self._trace_color, (tuple, list)):
            self._c_trace_color: tuple[Color, Color] = tuple(
                convert_color(c, Color) for c in self._trace_color
            )

        else:
            self._c_trace_color: Color = self._trace_color.copy()
            self._original_alpha = self._c_trace_color.a1

        if isinstance(self._trace_color, (list, tuple)) and len(self._trace_color) == 1:
            self._c_trace_color: Color = self._c_trace_color[0]
            self._original_alpha = self._c_trace_color.a1

        super().__init__(sync_id, self._bullet_image, parent)  # type: ignore

    @classmethod
    def bullet_image(cls) -> int:
        """Bullet texture ID."""
        return cls._bullet_image

    def _kill(self) -> None:
        if len(self._trace) > 0:
            if not self._trace_only:
                self._trace_only = True
                self.alive = False

                if self.param0 > 0:
                    explosion.draw(
                        delay=0.05,  # min(.01, .05 * (self.param0 / 96)),
                        size=Vec2().from_cartesian(self.param0 * 2, self.param0 * 2),
                        position=self.pos.copy(),
                    )

            return

        if not self._trace_only and self.param0 > 0:
            explosion.draw(
                delay=0.05,  # min(.01, .05 * (self.param0 / 96)),
                size=Vec2().from_cartesian(self.param0 * 2, self.param0 * 2),
                position=self.pos.copy(),
            )

        super().kill()

    def kill(self) -> None:
        if self._kill_next is not None:
            if self._kill_next <= 0:
                self._kill_next = None
                self._kill()

            else:
                self._kill_next -= 1

        else:
            self._kill_next = 1

    @classmethod
    def draw_at(
        cls,
        position: coord_t,
        size: coord_t,
        layer: int,
        *,
        rotation: float = 0,
    ) -> None:
        """Draw an entity at specified position and size."""
        if cls.bullet_image() is ...:
            cls.load_textures()

        renderer.draw_textured_quad(
            cls.bullet_image(),  # type: ignore
            position,
            size,
            rotate_angle=rotation,
            layer=layer,
        )

    def _gl_draw(
        self, delta_cal: float, layer: int = 0, draw_entity: bool = True
    ) -> None:
        if self._visibility_offset > self._lifetime:
            self._last_pos.length = 0
            self._lifetime += delta_cal
            return

        world_pos = pv.global_vars.get_world_position()
        resolution = pv.global_vars.resolution_screen

        draw = self.alive or (self._kill_next is not None and self._kill_next > 0)
        if draw:
            # calculate trace
            if self._show_trace and self._max_trace_length > 0:  # and delta_cal > 0:
                if len(self._trace) == 0:
                    img_offset = Vec2().from_polar(self.facing.angle, self.size.x / 2)
                    self._trace.append(self.pos.copy() - img_offset)
                    self._trace_len = 1

                else:
                    now_pos = self.pos.copy()
                    img_offset = Vec2().from_polar(self.facing.angle, self.size.x / 2)
                    trace_pos = now_pos - img_offset
                    new_delta = (trace_pos - self._trace[0]).length

                    if new_delta > 0:
                        # keep trace at max length
                        while (
                            self._current_trace_length + new_delta
                            > self._max_trace_length
                        ):
                            if len(self._trace) < 2:
                                break

                            diff = (self._trace.pop(-1) - self._trace[-1]).length
                            self._current_trace_length -= diff

                        # insert current trace pos at start
                        self._current_trace_length += new_delta

                        # remove image size from trace position (mortar trace starts at end)
                        self._trace.insert(0, trace_pos)

                        self._trace_len = len(self._trace)

            if (
                self.pos.x + (self._max_trace_length + self.size.x / 2) < world_pos.x
                or self.pos.x - (self._max_trace_length + self.size.x / 2)
                > world_pos.x + resolution.x
                or self.pos.y + (self._max_trace_length + self.size.y / 2) < world_pos.y
                or self.pos.y - (self._max_trace_length + self.size.y / 2)
                > world_pos.y + resolution.y
            ):
                self._last_pos.length = 0
                return

            if pv.global_vars.show_targets and not isinstance(
                self._target_pos, EllipsisType
            ):
                renderer.draw_line(
                    self.pos - world_pos,
                    self._target_pos - world_pos,
                    Color().from_255(255, 100, 0, 220),
                )
                renderer.draw_circle(
                    self._target_pos - world_pos,
                    self.size.x * 0.5,
                    32,
                    Color().from_255(255, 100, 0, 220),
                )

        else:
            new_len = self._current_trace_length - self.param1 * 0.5 * delta_cal
            if delta_cal == 0 or new_len <= 0:
                self._trace.clear()

            else:
                while self._current_trace_length > new_len:
                    if len(self._trace) < 2:
                        break

                    diff = (self._trace.pop(-1) - self._trace[-1]).length
                    self._current_trace_length -= diff

        # draw trace
        if self._show_trace and len(self._trace) > 1:
            if isinstance(self._c_trace_color, tuple):
                color: Color = fade(  # type: ignore
                    *self._c_trace_color,
                    min(self._lifetime / self._trace_fade_color_time, 1),
                )
                trace_mult = color.a1

            else:
                color: Color = self._c_trace_color.copy()
                trace_mult = self._original_alpha

            points: list[Vec2] = []
            colors: list[Color] = []
            for i in range(len(self._trace)):
                p1 = self._trace[i]

                # check if any of the positions is at 0/0
                if p1.length < 1:
                    continue

                if self._fade_trace:
                    color.a1 = trace_mult * (1 - (i / self._trace_len))

                points.append(p1 - world_pos)
                colors.append(color.copy())

            renderer.draw_lines(
                points,
                colors,
                thickness=(self.size.length / 3) * self._trace_width_mult,
            )

        if draw and not self._trace_only and draw_entity:
            self.facing *= -1
            super()._gl_draw(delta_cal)
            self._last_pos.xy = self.pos.xy

        else:
            self._lifetime += delta_cal


class Grenade(BulletDummy):
    _image_name: str = "grenade"
    _CID = DummyCIDs.grenade
    _trace_show = False
