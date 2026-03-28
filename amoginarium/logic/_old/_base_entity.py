"""
_base_entity.py
25. January 2024

defines the most basic form of an entity

Author:
Nilusink
"""
from __future__ import annotations
import pygame as pg
import typing as tp
import math as m

from amoginarium.shared.debugging import print_ic_style, CC
from amoginarium.graphics.render_bindings import renderer
from amoginarium.shared._entity_hints import BaseEntityLike
from amoginarium.logic.entities import Updated, Drawn
from amoginarium.shared.utility import Vec2

_next_entity_id = 0


class BaseEntity(pg.sprite.Sprite):
    """
    Base class for all entities

    Has no functionality for UI and logic other than ID and optional parent/children/root
    """
    __next_entity_id: int = 0  # class var

    _children: list[BaseEntityLike] = ...
    _current_t: float = 0
    _parent: BaseEntityLike | None

    def __init__(self, parent: BaseEntityLike | None = None) -> None:
        """
        Init BaseEntity
        :param parent: parent entity (optional)
        """
        super().__init__()
        self._children: list[BaseEntity] = []

        self.__id = BaseEntity.__next_entity_id
        BaseEntity.__next_entity_id += 1

        self._parent = parent

    @property
    def id(self) -> int:
        """:return: unique entity id (simplifies comparison)"""
        return self.__id

    @property
    def parent(self) -> BaseEntityLike:
        """:return: Parent entity or None"""
        return self._parent

    @property
    def root(self) -> BaseEntity | None:
        """return: Root entity or None"""
        return self._parent.root if self._parent else self

    @property
    def children(self) -> list[BaseEntityLike] | None:
        """return: List of children or None"""
        return self._children

    def update(self, delta: float) -> None:
        self._current_t += delta


class VisibleBaseEntity(BaseEntity):
    def gl_draw(self) -> None:
        for child in self._children:
            if hasattr(child, "gl_draw"):
                child.gl_draw()


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
            parent: BaseEntityLike = None
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
    _cid: str = ...
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
            parent: BaseEntityLike = None
    ) -> None:
        self._coalition = coalition

        size = Vec2().from_cartesian(1, 1) if size is ... else size
        self.facing = Vec2().from_cartesian(1, 0) if facing is ... else facing
        position = Vec2() if initial_position is ... else initial_position
        self.velocity = Vec2() if initial_velocity is ... else initial_velocity
        self.acceleration = Vec2()
        self._velocity_to_add = Vec2()
        self._acceleration_to_add = Vec2()

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

    @classmethod
    def cid(cls) -> str:
        if cls._cid is ...:
            raise ValueError("__cid is not defined for " + cls.__name__)

        return cls._cid

    @property
    def serializable(self) -> bool:
        return hasattr(self, "_cid")

    def to_dict(self) -> dict:
        if not hasattr(self, "_cid"):
            print_ic_style(
                f"{CC.fg.RED}Entity of type {self.__class__.__name__} is not"
                f"serializable{CC.ctrl.ENDL}",
            )

        return {
            "type": self.cid(),
            "pos": self.position
        }

    def add_velocity(self, value: Vec2) -> None:
        """
        add velocity to the entity and guarantee that it will be valid
        (for short bursts)
        """
        self._velocity_to_add += value

    def add_acceleration(self, value: Vec2) -> None:
        """
        add acceleration to the entity and guarantee that it will be valid
        (for long accelerations)
        """
        self._acceleration_to_add += value

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
        # self.acceleration += self._acceleration_to_add

        # update velocity and position
        self.velocity += (self._acceleration_to_add + self.acceleration) * delta + self._velocity_to_add
        self.position += self.velocity * delta
        self.acceleration.x *= 0

        self._velocity_to_add *= 0
        self._acceleration_to_add *= 0

        # re-calculate pygame stuff
        self.last_angle = self.velocity.angle

        self.update_rect()

        super().update(delta)

        # update children
        for child in self._children:
            child.update(delta)

    def kill(self, killed_by: tp.Self = ...) -> None:
        for child in self._children:
            if hasattr(child, "kill"):
                child.kill()

        super().kill()


class VisibleGameEntity(GameEntity):
    def __init__(
            self,
            size: Vec2 = ...,
            facing: Vec2 = ...,
            initial_position: Vec2 = ...,
            initial_velocity: Vec2 = ...,
            coalition: tp.Any = ...,
            parent: BaseEntityLike = None
    ) -> None:
        self._highlight = False
        super().__init__(
            size,
            facing,
            initial_position,
            initial_velocity,
            coalition,
            parent
        )

        self.add(Drawn)

    def highlight(self) -> None:
        self._highlight = True

    def stop_highlight(self) -> None:
        self._highlight = False

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x - self.size.x / 2,
            self.position.y - self.size.y / 2,
            self.size.x,
            self.size.y
        )

    def gl_draw(self) -> None:
        for child in self._children:
            if hasattr(child, "gl_draw"):
                child.gl_draw()


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
        super().gl_draw()


class LRImageEntity(VisibleGameEntity):
    _texture_left: int
    _texture_right: int

    def update(self, delta: float) -> None:
        super().update(delta)

    def gl_draw(
            self,
            draw_at: Vec2 = ...,
            size: Vec2 = ...,
            convert_global: bool = True
    ) -> None:
        if draw_at is not ...:
            pos = draw_at

        else:
            pos = self.world_position

        if size is ...:
            size = self.size


        renderer.draw_textured_quad(
            self._texture_right if self.facing.x < 0 else self._texture_left,
            pos - size / 2,
            size,
            convert_global=convert_global
        )
        super().gl_draw()
