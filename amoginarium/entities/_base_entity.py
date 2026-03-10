"""
_base_entity.py
25. January 2024

defines the most basic form of an entity

Author:
Nilusink
"""
from __future__ import annotations
# from OpenGL.GL import glRotated
# from icecream import ic
# noinspection PyPackageRequirements
import pygame as pg
import typing as tp
import math as m

# from ..base._linked import global_vars
from ..render_bindings import renderer
from ..logic import Vec2, rk4_update
from ..base import Updated, Drawn


class BaseEntity(pg.sprite.Sprite):
    """
    Base class for all entities

    Has no functionality for UI and logic other than ID and optional parent/children/root
    """
    __next_entity_id: int = 0  # class var

    _parent: BaseEntity | None = None  # instance var
    _children: list[BaseEntity] | None = None  # instance var
    _root: BaseEntity | None = None  # instance var

    def __init__(self, parent: BaseEntity | None = None) -> None:
        """
        Init BaseEntity
        :param parent: parent entity (optional)
        """
        super().__init__()

        self.__id = BaseEntity.__next_entity_id
        BaseEntity.__next_entity_id += 1

        self._parent = parent

    @property
    def id(self) -> int:
        """:return: unique entity id (simplifies comparison)"""
        return self.__id

    @property
    def parent(self) -> BaseEntity | None:
        """:return: Parent entity or None"""
        return self._parent

    @property
    def root(self) -> BaseEntity | None:
        """return: Root entity or None"""
        return self._parent.root

    @property
    def children(self) -> list[BaseEntity] | None:
        """return: List of children or None"""
        return self._children


class PositionedEntity(BaseEntity):
    """
    Basic Entity with absolute position and size
    """
    _position: Vec2
    _size: Vec2

    def __init__(
            self,
            position: Vec2,
            size: Vec2,
            parent: BaseEntity | None = None
    ) -> None:
        super().__init__(parent=parent)

        self._position = position
        self._size = size

    @property
    def position(self) -> Vec2:
        """:return: Absolute Position"""
        return self._position

    @position.setter
    def position(self, value: Vec2) -> None:
        """
        Set absolute positon
        :param value: new position
        """
        self._position = value

    @property
    def size(self) -> Vec2:
        """:return: Absolute Size"""
        return self._size

    @size.setter
    def size(self, value: Vec2) -> None:
        """
        Set absolute size
        :param value: new size
        """
        self._size = value


class GameEntity(PositionedEntity):
    facing: Vec2
    position: Vec2
    velocity: Vec2
    acceleration: Vec2

    def __init__(
            self,
            size: Vec2 = ...,
            facing: Vec2 = ...,
            initial_position: Vec2 = ...,
            initial_velocity: Vec2 = ...,
            coalition: tp.Any = ...,
            parent: BaseEntity = ...
    ) -> None:
        self._coalition = coalition

        size = Vec2.from_cartesian(1, 1) if size is ... else size
        self.facing = Vec2.from_cartesian(1, 0) if facing is ... else facing
        position = Vec2() if initial_position is ... else initial_position
        self.velocity = Vec2() if initial_velocity is ... else initial_velocity
        self.acceleration = Vec2()

        super().__init__(position, size, parent)

        self.update_rect()
        self._generate_collision_mask()
        self.add(Updated)

    @property
    def position_center(self) -> Vec2:
        """
        return the center of the sprite
        """
        return self.position + self.size / 2

    @property
    def world_position(self) -> Vec2:
        """
        return the position relative to the world center
        """
        return self.position - Updated.world_position

    @property
    def is_bullet(self) -> bool:
        return False

    @property
    def coalition(self) -> tp.Any:
        return self._coalition

    def _generate_collision_mask(self) -> None:
        """
        generate the mask used for precise collision
        """
        self.mask = pg.mask.Mask(self.size.xy, True)

    def on_ground(self) -> bool:
        return self.position.y + self.size.y > 1080

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x - self.size.x / 2,
            self.position.y - self.size.y / 2,
            self.size.x,
            self.size.y
        )

    def update(self, delta: float) -> None:
        # acceleration_func just returns self.acceleration (constant) or compute dynamically
        # def acc_func(pos, vel):
        #     return self.acceleration  # or compute based on pos/vel if needed
        #
        # self.position, self.velocity = rk4_update(
        #     self.position,
        #     self.velocity,
        #     acc_func,
        #     delta
        # )
        # update velocity and position
        self.velocity += self.acceleration * delta
        self.position += self.velocity * delta
        self.acceleration.x *= 0

        # re-calculate pygame stuff
        self.last_angle = self.velocity.angle

        self.update_rect()

    def kill(self, killed_by: tp.Self = ...) -> None:
        super().kill()


class VisibleGameEntity(GameEntity):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add(Drawn)

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x - self.size.x / 2,
            self.position.y - self.size.y / 2,
            self.size.x,
            self.size.y
        )

    def gl_draw(self) -> None:
        raise NotImplementedError(
            f"gl_draw wasn't implemented for \"{self.__class__.__name__}\""
        )


class ImageEntity(VisibleGameEntity):
    _original_image: pg.surface.Surface

    def __init__(self, texture_id: int, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._texture_id = texture_id

    def update(self, delta: float) -> None:
        super().update(delta)

    def gl_draw(self) -> None:
        renderer.draw_textured_quad(
            self._texture_id,
            (
                self.rect.x - Updated.world_position.x,
                self.rect.y - Updated.world_position.y
            ),
            (
                self.size.x,
                self.size.y
            ),
            rotate_angle=self.velocity.angle * (180 / m.pi)
        )


class LRImageEntity(VisibleGameEntity):
    _texture_left: int
    _texture_right: int

    def update(self, delta: float) -> None:
        super().update(delta)

    def gl_draw(self) -> None:
        renderer.draw_textured_quad(
            self._texture_right if self.facing.x < 0 else self._texture_left,
            self.world_position - self.size / 2,
            self.size
        )
