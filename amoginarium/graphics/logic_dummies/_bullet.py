"""
_bullet.py
31.03.2026

Bullet dummy entity

Author:
Nilusink
"""
from types import EllipsisType

from amoginarium.shared.utility import Vec2, color_t, Color, convert_color, convert_coord
from amoginarium.shared import DummyCIDs
from amoginarium.base._textures import textures
from amoginarium import pv

from ..render_bindings import renderer
from ._synced_entities import SyncedImageEntity, BaseGraphicsEntity
from ..entities._animation import explosion


BULLET_PATH = "bullet"


class BulletDummy(SyncedImageEntity):
    """
    ``param0`` explosion size
    ``param1`` velocity (length)
    """
    __slots__ = [
        "_spawn_time", "_visibility_offset", "_last_pos", "_target_pos", "_trace",
        "_trace_color"
    ]

    _cid = DummyCIDs.base_bullet
    _bullet_image: str = (BULLET_PATH, "x")

    def __init__(
        self,
        sync_id: int,
        spawn_time: float,
        size: int | Vec2 = 64,
        parent: BaseGraphicsEntity | None = None,
        no_gravity=False,
        visibility_offset: float = 0,
        target_pos: Vec2 | EllipsisType = ...,
        trace: bool = True,
        trace_color: color_t | EllipsisType = ...,
    ) -> None:
        if not isinstance(size, Vec2):
            size: Vec2 = Vec2().from_cartesian(size, size)  # type: ignore

        isize = size.xy
        _bullet_image, _ = textures.get_texture(
            self._bullet_image[0],
            isize,
            self._bullet_image[1]
        )

        self._spawn_time = spawn_time
        self._visibility_offset = visibility_offset
        self._last_pos: Vec2 = Vec2()
        if not isinstance(target_pos, EllipsisType):
            self._target_pos = convert_coord(target_pos, Vec2)

        else:
            self._target_pos = ...

        self._trace = trace

        if not isinstance(trace_color, EllipsisType):
            self._trace_color = convert_color(trace_color, Color)

        else:
            self._trace_color = Color().from_255(255, 255, 60)

        super().__init__(sync_id, _bullet_image, parent)

    def kill(self) -> None:
        if self.param0 > 0:
            explosion.draw(
                delay=.05,
                size=Vec2().from_cartesian(
                    self.param0 * 2,
                    self.param0 * 2
                ),
                position=self.pos.copy()
            )

        super().kill()

    def _gl_draw(self, delta_cal: float):
        if self._visibility_offset > 0:
            self._visibility_offset -= delta_cal
            self._last_pos.length = 0
            return

        world_pos = pv.global_vars.get_world_position()
        screen_pixels = pv.global_vars.screen_pixels
        if (
            self.pos.x + self.size.x / 2 < world_pos.x
            or self.pos.x - self.size.x / 2 > world_pos.x + screen_pixels.x
            or self.pos.y + self.size.y / 2 < world_pos.y
            or self.pos.y - self.size.y / 2 > world_pos.y + screen_pixels.y
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

        # draw trace
        if not self.alive:
            self._last_pos.length = 0

        if self._trace and self._last_pos.length > 0:
            self._trace_color.a1 = min([1, self.param1 / 10000])
            renderer.draw_thick_line(
                self.pos - world_pos,
                self._last_pos - world_pos,
                self._trace_color,  # ignore: type
                self.size.length / 3,
            )

        super()._gl_draw(delta_cal)
        self._last_pos.xy = self.pos.xy


class MortarShell(BulletDummy):
    _bullet_image: str = ("mortar_shell", "")
    _cid = DummyCIDs.mortar_bullet


class Grenade(BulletDummy):
    _bullet_image: str = ("grenade", "")
    _cid = DummyCIDs.grenade
