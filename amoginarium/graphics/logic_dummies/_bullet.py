"""
_bullet.py
31.03.2026

Bullet dummy entity

Author:
Nilusink
"""
import typing as tp

from amoginarium.shared.utility import Vec2, color_t
from amoginarium.shared import DummyCIDs
from amoginarium.base._textures import textures

from ._synced_entities import SyncedImageEntity, BaseGraphicsEntity


BULLET_PATH = "bullet"


class BulletDummy(SyncedImageEntity):
    __slots__ = ["_spawn_time"]

    _cid = DummyCIDs.base_bullet
    _bullet_image: str = (BULLET_PATH, "x")

    def __init__(
            self,
            sync_id: int,
            spawn_time: float,
            size: int = 64,
            parent: BaseGraphicsEntity | None = None,
            no_gravity=False,
            visibility_offset: float = 0,
            trace: bool = True,
            trace_color: color_t = ...
    ) -> None:
        if not isinstance(size, Vec2):
            size = Vec2().from_cartesian(size, size)

        isize = size.xy
        _bullet_image, _ = textures.get_texture(
            self._bullet_image[0],
            isize,
            self._bullet_image[1]
        )

        self._spawn_time = spawn_time

        super().__init__(sync_id, _bullet_image, parent)


class MortarShell(BulletDummy):
    _bullet_image: str = ("mortar_shell", "")
    _cid = DummyCIDs.mortar_bullet


class Grenade(BulletDummy):
    _bullet_image: str = ("grenade", "")
    _cid = DummyCIDs.grenade
