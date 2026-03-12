"""
_items.py
12.03.2026

various items that are not weapons

Author:
Nilusink
"""
from ..logic import coord_t, convert_coord, Vec2
from ..base._textures import textures
from ..base import CollisionDestroyed
from ._base_entity import PositionedEntity
from ._entity_hints import PlayerLike, BaseEntityLike


class BaseItem(PositionedEntity):
    _image_texture: int = ...
    _image_name: tuple[str, str] | str = "bullet"
    _image_size: tuple[int, int] = (32, 32)
    _max_uses: int = 1

    @classmethod
    def load_textures(cls) -> None:
        if cls._image_texture is not ...:
            return

        if isinstance(cls._image_name, str):
            cls._image_texture = textures.get_texture(
                cls._image_name,
                cls._image_size
            )

        else:
            cls._image_texture = textures.get_texture(
                cls._image_name[1],
                cls._image_size,
                scope=cls._image_name[0]
            )

    def __init__(
            self,
            parent: PlayerLike,
            parent_position_offset: coord_t
    ) -> None:
        self._position_offset = convert_coord(parent_position_offset, Vec2)
        self._uses_left = self._max_uses

        super().__init__(
            parent.position + self._position_offset,
            Vec2.from_cartesian(*self._image_size),
            parent
        )

    @property
    def max_uses(self) -> int:
        return self._max_uses

    @property
    def uses_left(self) -> int:
        return self._uses_left

    def use(self) -> None:
        raise NotImplementedError

    def stop_use(self) -> None:
        raise NotImplementedError

    def update(self, delta: float) -> None:
        pass

    def gl_draw(self) -> None:
        pass


class Shield(BaseItem):
    _image_texture: int = ...
    _image_name: tuple[str, str] | str = "bullet"
    _image_size: tuple[int, int] = (32, 32)
    _max_uses: int = -1

    def use(self) -> None:
        ...

    def hit(self, damage: float, hit_by: BaseEntityLike = ...) -> None:
        ...

    def kill(self, killed_by=...) -> None:
        ...