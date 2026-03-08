"""
_groups.py
25. January 2024

Defines sprite groups

Author:
Nilusink
"""
from contextlib import suppress
# from icecream import ic
import pygame as pg
import typing as tp
import numpy as np
from icecream import ic

from ..logic import Vec2, is_related, Color, coord_t, convert_coord
from ..render_bindings import renderer
from ..debugging import timeit
# from ..debugging import run_with_debug


class _BaseGroup(pg.sprite.Group):
    def gl_draw(self) -> None:
        """
        draw sprites using the .gl_draw function
        """
        for sprite in self.sprites():
            sprite.gl_draw()

    @staticmethod
    def entities_in_circle(
        entities: list[pg.sprite.Sprite],
        center: Vec2,
        radius: float
    ) -> list[tuple[float, tp.Any]]:
        """
        check which of the given entities are in the circle
        """
        out = []

        for sprite in entities:
            delta = sprite.position - center

            if delta.length <= radius:
                out.append((delta.length, sprite))

        return sorted(out, key=lambda r: r[0])

    def get_entities_in_circle(
        self,
        center: Vec2,
        radius: float
    ) -> list[tuple[float, tp.Any]]:
        """
        get all entities inside a circle, sorted by distance (closest first)
        """
        return self.entities_in_circle(self.sprites(), center, radius)


class _Bullets(_BaseGroup):
    ...


class _Updated(_BaseGroup):
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


class _Drawn(_BaseGroup):
    ...


class _Walls(_BaseGroup):
    ...


class _Players(_BaseGroup):
    _spawn_point: Vec2

    @property
    def spawn_point(self) -> Vec2:
        """
        player spawn point
        """
        return Updated.world_position + self._spawn_point.copy()

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
        min_pos = Vec2.from_cartesian(np.inf, 0)

        for sprite in self.sprites():
            if sprite.position.x > max_pos.x:
                max_pos = sprite.position.copy()

            if sprite.position.x < min_pos.x:
                min_pos = sprite.position.copy()

        return min_pos, max_pos


class _WallCollider(_BaseGroup):
    """
    requires::

        on_wall: bool
    """
    @staticmethod
    def collides_with(
            sprite
    ) -> bool | tuple[pg.sprite.Sprite, tuple[int, int]]:
        for wall in Walls.sprites():
            sprite: tp.Any
            wall: tp.Any

            # use collide_rect first, because performance and stuff
            if pg.sprite.collide_rect(wall, sprite):
                pos = wall.collide(sprite)
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


class _GravityAffected(_BaseGroup):
    """
    required methods / variables:

        velocity: Vec2
        position: Vec2
    """

    @property
    def gravity(self) -> float:
        return 9.81 * 50

    def calculate_gravity(self, _delta: float) -> None:
        for sprite in self.sprites():
            sprite: tp.Any

            sprite.acceleration.y = self.gravity

            # with suppress(AttributeError):
            #     if sprite.on_ground and sprite.velocity.y > 0:
            #         while sprite.on_ground:
            #             sprite.position.y -= 0.01

            #         sprite.position.y += 0.01
            #         sprite.velocity.y = 0


class _FrictionXAffected(_BaseGroup):
    @property
    def friction(self) -> float:
        return 60

    def calculate_friction(self, delta: float) -> None:
        for sprite in self.sprites():
            with suppress(AttributeError):
                sprite.acceleration.x = -sprite.velocity.x / 100
                sprite.acceleration.x *= self.friction


class _HasBars(_BaseGroup):
    """
    required methods / variables::

        hp: float
        max_hp: float
    """

    def gl_draw(self) -> None:
        for sprite in self.sprites():
            with suppress(KeyError):
                sprite: tp.Any
                bar_height = 7

                # draw health bar
                max_len = sprite.size.x
                now_len = (sprite.hp / sprite.max_hp) * max_len

                bar_start = sprite.world_position.copy()
                bar_start.x -= sprite.size.x / 2
                bar_start.y += sprite.size.y / 2 + 10

                t = now_len / max_len
                color = Color.fade(
                    Color.from_255(255, 0, 0),
                    Color.from_255(180, 90, 20),
                    t * 2
                ) if t < .5 else Color.fade(
                    Color.from_255(180, 90, 20),
                    Color.from_255(0, 255, 0),
                    (t - .5) * 2
                )

                renderer.draw_rect(
                    bar_start,
                    Vec2.from_cartesian(max_len, bar_height),
                    (0, 0, 0, .5)
                )
                renderer.draw_rect(
                    bar_start,
                    Vec2.from_cartesian(now_len, bar_height),
                    color
                )

                # draw mag / reload bar
                mag_n, mag_v = sprite.weapon.get_mag_state(1000)
                now_len = (mag_n / 1000) * max_len
                renderer.draw_rect(
                    bar_start + Vec2.from_cartesian(0, 1.5 * bar_height),
                    Vec2.from_cartesian(max_len if now_len else 0, bar_height),
                    (0, 0, 0, .5)
                )
                renderer.draw_rect(
                    bar_start + Vec2.from_cartesian(0, 1.5 * bar_height),
                    Vec2.from_cartesian(now_len, bar_height),
                    (.55, .55, 1, 1)
                )


class _WallBouncer(_BaseGroup):
    """
    required methods / variables::

        velocity: Vec2
        position: Vec2
    """
    def update(self) -> None:
        for sprite in self.sprites():
            with suppress(AttributeError):
                sprite: tp.Any
                if 10 > sprite.position.x:
                    sprite.velocity.x = abs(sprite.velocity.x)

                elif sprite.position.x > 1920:
                    print(sprite.position)
                    sprite.velocity.x = -abs(sprite.velocity.x)

                if 10 > sprite.position.y:
                    sprite.velocity.y = abs(sprite.velocity.y)

                elif sprite.position.y > 900:
                    sprite.velocity.y = -abs(sprite.velocity.y)


class _CollisionDestroyed(_BaseGroup):
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
    @timeit(10)
    def update(self) -> None:
        for sprite in CollisionDestroyed.sprites():

            with suppress(AttributeError):
                for other in self.sprites():
                    sprite: tp.Any
                    other: tp.Any

                    if 1:
                        if all([
                            pg.sprite.collide_rect(sprite, other),
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
        start = sprite.position - sprite.size / 2
        end = sprite.position + sprite.size / 2

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
Drawn = _Drawn()
Walls = _Walls()
Players = _Players()
Bullets = _Bullets()
HasBars = _HasBars()
Updated = _Updated()
WallBouncer = _WallBouncer()
WallCollider = _WallCollider()
GravityAffected = _GravityAffected()
FrictionXAffected = _FrictionXAffected()
CollisionDestroyed = _CollisionDestroyed()
