"""
_bullet.py
31.03.2026

Bullet dummy entity

Author:
Nilusink
"""
from icecream import ic

from amoginarium.shared.debugging import run_with_debug
from amoginarium.shared.utility import Vec2, color_t
from amoginarium.shared import DummyCIDs
from amoginarium.base._textures import textures

from ._synced_entities import SyncedImageEntity, BaseGraphicsEntity
from ..entities._animation import explosion


BULLET_PATH = "bullet"


class BulletDummy(SyncedImageEntity):
    """
    ``param0`` explosion size
    """
    __slots__ = ["_spawn_time", "_visibility_offset"]

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
        trace: bool = True,
        trace_color: color_t = ...,
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

        super().__init__(sync_id, _bullet_image, parent)

    @run_with_debug()
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
            return

        super()._gl_draw(delta_cal)


class MortarShell(BulletDummy):
    _bullet_image: str = ("mortar_shell", "")
    _cid = DummyCIDs.mortar_bullet


class Grenade(BulletDummy):
    _bullet_image: str = ("grenade", "")
    _cid = DummyCIDs.grenade
