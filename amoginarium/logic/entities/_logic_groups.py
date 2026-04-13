"""
_groups.py
25. January 2024

Defines sprite groups

Author:
Nilusink

"""
from contextlib import suppress
from icecream import ic
import pygame as pg
import typing as tp
import numpy as np

from amoginarium.shared.debugging import cum_timer

from ...shared.utility import Vec2, is_related, convert_coord, raycast_mask, \
    normalize_angle, coord_t
from ...shared import GlobalVars, BaseLogicEntityLike
from ... import pv

from ._base_group import BaseGroup
from ._collision_groups import GridSystem, GridCell


class _Bullets(BaseGroup):
    ...


class _Updated(BaseGroup):
    world_position: Vec2
    pixel_per_meter: Vec2
    screen_size: Vec2

    def __init__(self, *args) -> None:
        self.world_position = Vec2()
        super().__init__(*args)

    def out_of_bounds_x(self, sprite, margin: float = 0) -> bool:
        return any([
            self.world_position.x + margin > sprite.position.x,
            sprite.position.x + margin > self.world_position.x + 1920
        ])

    def load_textures(self) -> None:
        """
        load all textures
        """
        # get the different types of entities
        types = tuple(set([s.__class__ for s in self.sprites()]))

        # load the textures for each different type
        for t in types:

            # only load textures if the type has a function
            # to load the textures
            if hasattr(t, "load_textures"):
                t.load_textures()


class _Walls(BaseGroup):
    # @timeit(10)
    def walls_in_line(
            self,
            start: coord_t,
            end: coord_t
    ) -> list:
        start = convert_coord(start, tuple)
        end = convert_coord(end, tuple)
        walls_hit = []
        for wall in self.sprites():
            if raycast_mask(wall, start, end, 2):
                walls_hit.append(wall)

        return walls_hit


class _Players(BaseGroup):
    _spawn_point: Vec2 = None

    @property
    def spawn_point(self) -> Vec2 | None:
        """
        player spawn point
        """
        if self._spawn_point:
            return Updated.world_position.copy() + self._spawn_point.copy()

        return None

    @spawn_point.setter
    def spawn_point(self, point: Vec2) -> None:
        self._spawn_point = point

    def get_max_position(self) -> Vec2:
        max_pos = Vec2()
        for sprite in self.sprites():
            if sprite.position.x > max_pos.x:
                max_pos = sprite.position.copy()

        return max_pos

    def get_min_position(self) -> Vec2:
        min_pos = np.inf
        for sprite in self.sprites():
            if sprite.position.x < min_pos.x:
                min_pos = sprite.position.copy()

        return min_pos

    def get_position_extremes(self) -> tuple[Vec2, Vec2]:
        """
        get min and max positions

        :returns: min, max
        """
        max_pos = Vec2()
        min_pos = Vec2().from_cartesian(np.inf, np.inf)

        for sprite in self.sprites():
            if sprite.position.x > max_pos.x:
                max_pos = sprite.position.copy()

            if sprite.position.x < min_pos.x:
                min_pos = sprite.position.copy()

        return min_pos, max_pos


class _WallCollider(BaseGroup):
    """
    requires::

        on_wall: bool
    """

    @staticmethod
    def collides_with(
            sprite
    ) -> bool | tuple[pg.sprite.Sprite, tuple[int, int]]:
        for group in GridSystem.get_cells_by_pos(sprite.rect.topleft[0], sprite.rect.bottomright[0]):
            for wall in group.walls.sprites():
                if pg.sprite.collide_rect(wall, sprite):
                    pos = wall.collide(sprite)
                    if pos is not None:
                        return wall, pos
        return False

    @staticmethod
    @cum_timer.time_this
    def collides_with_groups(
            sprite,
            groups: list[GridCell]
    ) -> bool | tuple[pg.sprite.Sprite, tuple[int, int]]:
        for group in groups:
            for wall in group.walls.sprites():
                if pg.sprite.collide_rect(wall, sprite):
                    pos = wall.single_rect_collide(sprite)
                    if pos is not None:
                        return wall, pos
        return False

    @staticmethod
    def on_ground(
            sprite,
            alt_pos: coord_t = ...,
            alt_size: coord_t = ...
    ) -> bool | pg.sprite.Sprite:
        pos = sprite.position
        size = sprite.size

        if alt_pos is not ...:
            pos = convert_coord(alt_pos, Vec2)

        if alt_size is not ...:
            size = convert_coord(alt_size, Vec2)

        for wall in Walls.sprites():
            sprite: tp.Any
            wall: tp.Any

            if all([
                wall.position.y
                <= pos.y + size.y / 2,
                pos.y - size.y / 2
                <= wall.position.y + 20,

                wall.position.x
                <= pos.x + size.x / 4,
                pos.x - size.x / 4
                <= wall.position.x + wall.size.x
            ]):
                return wall

        return False


class _GravityAffected(BaseGroup):
    """
    required methods / variables:

        velocity: Vec2
        position: Vec2
    """

    @property
    def gravity(self) -> float:
        return 9.81 * pv.global_vars.get_acceleration_factor()

    def calculate_gravity(self, _delta: float) -> None:
        for sprite in self.sprites():
            sprite: tp.Any

            sprite.acceleration.y = self.gravity


class _FrictionXAffected(BaseGroup):
    @property
    def friction(self) -> float:
        return 60

    def calculate_friction(self, delta: float) -> None:
        for sprite in self.sprites():
            with suppress(AttributeError):
                sprite.acceleration.x -= sprite.velocity.x / 100
                sprite.acceleration.x *= self.friction


class _WallBouncer(BaseGroup):
    """
    required methods / variables::

        velocity: Vec2
        position: Vec2
        in_wall: Vec2 | None (optional, set by update)
    """

    def update(self) -> None:
        for sprite in self.sprites():
            with suppress(AttributeError):
                sprite: tp.Any
                in_wall = sprite.collision

                if not in_wall:
                    sprite.in_wall = None
                    continue

                wall, pos = in_wall
                delta = Vec2().from_cartesian(*pos)
                delta.angle = normalize_angle(delta.angle)
                sprite.in_wall = delta

                if hasattr(sprite, "_bounce_friction"):
                    sprite.velocity *= sprite._bounce_friction

                pi4 = np.pi / 4
                # ic(pi4, delta.xy, delta.angle, pos, sprite.position.xy)
                if pi4 <= delta.angle < 3 * pi4:
                    sprite.velocity.x = abs(sprite.velocity.x)

                elif 3 * pi4 <= delta.angle < 5 * pi4:
                    print(sprite.position)
                    sprite.velocity.x = -abs(sprite.velocity.x)

                elif 5 * pi4 <= delta.angle < 7 * pi4:
                    sprite.velocity.y = abs(sprite.velocity.y)

                else:
                    sprite.velocity.y = -abs(sprite.velocity.y)


class _CollisionDestroyed(BaseGroup):
    """
    required methods / variables::

        damage: float #
        (optional, use if collision should damage the other object)
        hp: float # (optional, sprite should either have damage or hp)
        hit(damage: float) -> None
        kill() -> None
    """

    @staticmethod
    def dynamic_collide(a: pg.sprite.Sprite, b: pg.sprite.Sprite) -> bool:
        """
        use different methods depending on what is being collided
        """
        if a.is_bullet and b.is_bullet:
            return _CollisionDestroyed.point_in_sprite(a, b.position.xy)

        if a.is_bullet:
            return _CollisionDestroyed.point_in_sprite(b, a.position.xy)

        if b.is_bullet:
            return _CollisionDestroyed.point_in_sprite(b, a.position.xy)

        return pg.sprite.collide_rect(a, b)

    # @profile
    # @timeit(10)
    def update(self) -> None:
        # todo: WHAT THE HELL IS THIS
        return
        for sprite in CollisionDestroyed.sprites():

            with suppress(AttributeError):
                for other in self.sprites():
                    # pg.sprite.collide_mask()

                    if 1:
                        if all([
                            pg.sprite.collide_mask(sprite, other),
                            not is_related(sprite, other, 2)
                        ]):
                            try:
                                dmg = other.damage

                            except AttributeError:
                                dmg = 0

                            sprite.hit(dmg, other)

                            with suppress(AttributeError):
                                hp = other.hp
                                if dmg != 0:
                                    sprite.hit_someone(target_hp=hp)

                            # bullet is sprite
                            try:
                                dmg = sprite.damage

                            except AttributeError:
                                dmg = 0

                            other.hit(dmg, sprite)

                            with suppress(AttributeError):
                                hp = sprite.hp
                                if dmg != 0:
                                    other.hit_someone(target_hp=hp)

    @staticmethod
    def size_collide(sprite1, sprite2) -> bool:
        # check for the first sprite to be in the second
        collision_distance = sprite1.size.length + sprite2.size.length
        return (
                sprite1.position_center - sprite2.position_center
        ).length <= collision_distance

    @staticmethod
    def point_in_sprite(sprite, point: tuple) -> bool:
        # start = sprite.position - sprite.size / 2
        # end = sprite.position + sprite.size / 2
        start = convert_coord(sprite.rect.topleft, Vec2)
        end = convert_coord(sprite.rect.bottomright, Vec2)

        return all([
            start.x <= point[0] <= end.x,
            start.y <= point[1] <= end.y
        ])

    @staticmethod
    def box_collide(sprite1, sprite2) -> bool:
        sprite1_pos = sprite1.position
        sprite2_pos = sprite2.position
        sprite1_size = sprite1.size
        sprite2_size = sprite2.size

        sprite1_center = sprite1.position_center
        sprite2_center = sprite2.position_center

        return all([
            sprite1_pos.x < sprite2_center.x < sprite1_pos.x + sprite1_size.x,
            sprite1_pos.y < sprite2_center.y < sprite1_pos.y + sprite1_size.y
        ]) or all([
            sprite2_pos.x < sprite1_center.x < sprite2_pos.x + sprite2_size.x,
            sprite2_pos.y < sprite1_center.y < sprite2_pos.y + sprite2_size.y
        ])


# initialize groups
Walls = _Walls()
Players = _Players()
Bullets = _Bullets()
Updated = _Updated()
WallBouncer = _WallBouncer()
WallCollider = _WallCollider()
GravityAffected = _GravityAffected()
FrictionXAffected = _FrictionXAffected()
CollisionDestroyed = _CollisionDestroyed()
