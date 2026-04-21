"""
_bullet.py
31.03.2026

Bullet dummy entity

Author:
Nilusink
"""
from icecream import ic
from types import EllipsisType

from amoginarium.shared.utility import Vec2, get_default, Color, convert_color
from amoginarium.shared.utility import convert_coord, fade
from amoginarium.shared import DummyCIDs
from amoginarium.base._textures import textures
from amoginarium import pv

from ..entities._animation import explosion
from ..render_bindings import renderer
from ._synced_entities import SyncedImageEntity, BaseGraphicsEntity


BULLET_PATH = "bullet"


class BulletDummy(SyncedImageEntity):
    """
    ``param0`` explosion size
    ``param1`` velocity (length)
    """
    __slots__ = [
        "_spawn_time", "_visibility_offset", "_last_pos", "_target_pos", "_trace",
        "_trace_color", "_show_trace", "_current_trace_length", "_max_trace_length",
        "_fade_trace", "_original_alpha", "_trace_len", "_trace_only"
    ]

    _cid = DummyCIDs.base_bullet
    _default_size: Vec2 = Vec2().from_cartesian(64, 64)
    _bullet_image: str = (BULLET_PATH, "x")
    _default_trace_color: Color | tuple[Color, Color] = Color().from_255(255, 255, 60)
    _fade_color_time: float = 1.5  # only applies if two colors are specified
    _default_trace_length: float = 100  # length in coords
    _default_show_trace: bool = True
    _default_fade_trace: bool = True

    def __init__(
        self,
        sync_id: int,
        spawn_time: float,
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

        isize = size.xy
        _bullet_image, _ = textures.get_texture(
            self._bullet_image[0],
            isize,
            self._bullet_image[1]
        )

        self._trace_only = False
        self._trace_len = 1
        self._spawn_time = spawn_time
        self._visibility_offset = visibility_offset
        self._last_pos: Vec2 = Vec2()
        self._trace = []
        self._current_trace_length = 0
        self._max_trace_length = (
            trace_length if trace_length is not ... else self._default_trace_length
        )
        self._fade_trace = (
            fade_trace if trace_length is not ... else self._default_fade_trace
        )
        self._show_trace = (
            show_trace if show_trace is not ... else self._default_show_trace
        )

        if not isinstance(target_pos, EllipsisType):
            self._target_pos = convert_coord(target_pos, Vec2)

        else:
            self._target_pos = ...

        if not isinstance(trace_color, EllipsisType):
            if isinstance(trace_color, tuple):
                self._trace_color: tuple[Color, Color] = (
                    convert_color(c, Color) for c in trace_color
                )
            
            else:
                self._trace_color: Color = convert_color(trace_color, Color)
                self._original_alpha = self._trace_color.a1

        else:
            if isinstance(self._default_trace_color, tuple) or isinstance(
                self._default_trace_color, list
            ):
                self._trace_color: tuple[Color, Color] = tuple(
                    convert_color(c, Color) for c in self._default_trace_color
                )

            else:
                self._trace_color: Color = self._default_trace_color.copy()
                self._original_alpha = self._trace_color.a1

        super().__init__(sync_id, _bullet_image, parent)

    def kill(self) -> None:
        if len(self._trace) > 0:
            if not self._trace_only:
                self._trace_only = False
                self.alive = False

                if self.param0 > 0:
                    explosion.draw(
                        delay=.05,  # min(.01, .05 * (self.param0 / 96)),
                        size=Vec2().from_cartesian(self.param0 * 2, self.param0 * 2),
                        position=self.pos.copy(),
                    )

            return

        if not self._trace_only:
            if self.param0 > 0:
                explosion.draw(
                    delay=.05,  # min(.01, .05 * (self.param0 / 96)),
                    size=Vec2().from_cartesian(
                        self.param0 * 2,
                        self.param0 * 2
                    ),
                    position=self.pos.copy()
                )

        super().kill()

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        if self._visibility_offset > self._lifetime:
            self._last_pos.length = 0
            self._lifetime += delta_cal
            return

        world_pos = pv.global_vars.get_world_position()
        resolution = pv.global_vars.resolution_screen
        if self.alive:
            # calculate trace
            if self._show_trace and self._max_trace_length > 0: # and delta_cal > 0:
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
                        while self._current_trace_length + new_delta > self._max_trace_length:
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
                    Color().from_255(255, 100, 0, 220)
                )
                renderer.draw_circle(
                    self._target_pos - world_pos,
                    self.size.x * .5,
                    32,
                    Color().from_255(255, 100, 0, 220)
                )

        else:
            new_len = self._current_trace_length - self.param1 * .5 * delta_cal
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
            if isinstance(self._trace_color, tuple):
                color: Color = fade(
                    *self._trace_color, min(self._lifetime / self._fade_color_time, 1)
                )
                trace_mult = color.a1

            else:
                color: Color = self._trace_color.copy()
                trace_mult = self._original_alpha

            for i in range(len(self._trace)-1):
                p1 = self._trace[i]
                p2 = self._trace[i+1]

                # check if any of the positions is at 0/0
                if p1.length * p2.length < 1:
                    continue

                if self._fade_trace:
                    color.a1 = trace_mult * (1 - (i / self._trace_len))

                renderer.draw_thick_line(
                    p1 - world_pos,
                    p2 - world_pos,
                    color,  # ignore: type
                    thickness=self.size.length / 3,
                )

        if self.alive:
            super()._gl_draw(delta_cal)
            self._last_pos.xy = self.pos.xy


class MortarShell(BulletDummy):
    _bullet_image: str = ("mortar_shell", "")
    _cid = DummyCIDs.mortar_bullet
    _default_trace_color = Color().from_1(1, 1, 1, .6)
    _default_trace_length = 200


class Grenade(BulletDummy):
    _bullet_image: str = ("grenade", "")
    _cid = DummyCIDs.grenade
    _default_show_trace = False
