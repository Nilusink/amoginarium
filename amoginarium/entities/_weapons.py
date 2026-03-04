"""
_weapons.py
26. January 2024

minigun go brrrrrt

Author:
Nilusink
"""
from time import perf_counter
from random import randint
import typing as tp
# from threading import Thread
# import time

from ..base import GravityAffected, CollisionDestroyed, Bullets, Updated, Drawn
from ..audio import PresetEffect, LargeExplosion, Shotgun, sound_effect_wrapper
from ..audio import ContinuousSoundEffect
from ..audio import Minigun as MinigunSound, AK47 as AK47Sound
from ..logic import Vec2, Color, convert_coord, coord_t
from ._base_entity import ImageEntity, Entity
from ..render_bindings import renderer
from ..shared import global_vars
from ..base._textures import textures
from ..animations import explosion
from ..base import WallCollider

BULLET_PATH = "bullet"


class Bullet(ImageEntity):
    _bullet_image: str = (BULLET_PATH, "x")
    _casing_image: str = (BULLET_PATH, "")
    _base_damage: float = 1

    def __new__(cls, *args, **kwargs) -> "Bullet":
        return super(Bullet, cls).__new__(cls)

    def __init__(
            self,
            parent: Entity,
            coalition: tp.Any,
            initial_position: Vec2,
            initial_velocity: Vec2,
            base_damage: float = 1,
            casing: bool = False,
            time_to_life: float = 2,
            explosion_radius: float = -1,
            explosion_damage: float = 0,
            target_pos: Vec2 = ...,
            size: int = 10
    ) -> None:
        size = Vec2.from_cartesian(size, size)
        self._casing = casing
        self._parent = parent
        self._base_damage = base_damage
        self._ttl = time_to_life
        self._initial_velocity = initial_velocity
        self._explosion_radius = explosion_radius
        self._explosion_damage = explosion_damage
        self._target_pos = target_pos

        self._start_time = perf_counter()

        # load textures
        self._bullet_texture, _ = textures.get_texture(BULLET_PATH, size.xy, "x")
        self._casing_texture, _ = textures.get_texture(BULLET_PATH, size.xy, "x")
        texture_id = self._bullet_texture

        super().__init__(
            texture_id=texture_id,
            size=size,
            initial_position=initial_position.copy(),
            initial_velocity=initial_velocity.copy(),
            coalition=coalition
        )

        self.add(GravityAffected)

        if not casing:
            self.add(Bullets, CollisionDestroyed)

    @property
    def on_ground(self) -> bool:
        return WallCollider.collides_with(self)

    @property
    def damage(self) -> float:
        """
        get bullet damage
        """
        if self._casing:
            return 0

        # calculate damage based on base_damage and velocity
        x = max(self._initial_velocity.length, 800)

        speed_mult = 1 + (
                (self.velocity.length - 1300) / x
        ) * .5
        damage = self._base_damage * speed_mult

        # ic(damage)

        return damage

    @property
    def parent(self) -> Entity:
        return self._parent

    @property
    def is_bullet(self) -> bool:
        return True

    def hit(self, _damage: float, hit_by: tp.Self = ...) -> None:
        self.kill(killed_by=hit_by)

    def hit_someone(self, target_hp: float) -> None:
        self.kill()

    def update(self, delta):
        self._ttl -= delta

        if any([
            self.position.y > 2000,
            self.position.x < Updated.world_position.x - 2000,
            self.position.x > Updated.world_position.x + 4000,
            self._ttl <= 0,
            self.on_ground
        ]):
            self.kill()
            return

        # double gravity (because why not)
        self.acceleration.y *= 2

        super().update(delta)

    def kill(self, killed_by: tp.Self = ...) -> None:
        if all([
            self._casing,
            not Updated.out_of_bounds_x(self)
        ]):
            self.position.y -= self.size.y / 2
            self.remove(
                Updated,
                CollisionDestroyed,
                GravityAffected
            )
            return

        # explode
        if self._explosion_radius > 0:
            for d, entity in CollisionDestroyed.get_entities_in_circle(
                    self.position,
                    self._explosion_radius
            ):
                if all([
                    entity != self,
                    entity.__class__ is not killed_by.__class__
                ]):
                    entity.hit(
                        (1 - .8 * d / self._explosion_radius)
                        * self._explosion_damage,
                        hit_by=self
                    )

            explosion.draw(
                delay=.05,
                size=Vec2.from_cartesian(
                    self._explosion_radius * 2,
                    self._explosion_radius * 2
                ),
                position_reference=self
            )

            if self._explosion_radius > 64:
                exp = LargeExplosion()
                exp.volume = .35
                exp.play()

            # sounds like shit
            # elif self._explosion_radius < 16:
            #     exp = SmallExplosion()
            #     exp.volume = .5
            #     exp.play()

        self.remove(Drawn)
        super().kill()

    def gl_draw(self) -> None:
        if not self._casing:
            if self._bullet_texture is ...:
                renderer.draw_circle(
                    self.world_position,
                    self.size.x * .5,
                    8,
                    Color.from_255(255, 255, 60)
                )

                if global_vars.show_targets and self._target_pos is not ...:
                    renderer.draw_line(
                        self.world_position,
                        self._target_pos - Updated.world_position,
                        Color.from_255(255, 100, 0, 220)
                    )
                    renderer.draw_circle(
                        self._target_pos - Updated.world_position,
                        self.size.x * .5,
                        32,
                        Color.from_255(255, 100, 0, 220)
                    )

                return

            # draw image if given
            self._texture_id = self._bullet_texture

        else:
            self._texture_id = self._casing_texture

        return super().gl_draw()


class BaseWeapon:
    _image_name: str = "bullet"
    _image_size: tuple[int, int] = (64, 64)
    _image_offset: Vec2 = Vec2.from_cartesian(0, 15)
    _image_rotate_anchor: Vec2 = ...
    _current_recoil_time: float = 0
    _current_sound_time: float = 0
    _current_reload_time: float = 0
    _mag_state: int = 0
    _recoil_factor: float
    _bullet_speed: float
    _recoil_time: float
    _reload_time: float
    _mag_size: int

    def __init__(
            self,
            parent,
            reload_time: float,
            recoil_time: float,
            recoil_factor: float,
            mag_size: int,
            inaccuracy: float,
            bullet_speed: float,
            barrel_length: float,  # where bullets spawn
            parent_position_offset: Vec2 | tuple[float, float],
            bullet_size: int = 10,
            bullet_damage: float = 1,
            bullet_explosion_radius: float = -1,
            bullet_explosion_damage: float = 0,
            drop_casings: bool = False,
            bullet_lifetime=2,
            sound_effect: type[ContinuousSoundEffect | PresetEffect] = ...
    ) -> None:
        self.parent = parent
        self._coalition = parent.coalition
        self._mag_size = mag_size
        self._inaccuracy = inaccuracy
        self._reload_time = reload_time
        self._recoil_time = recoil_time
        self._reload_time = reload_time
        self._bullet_speed = bullet_speed
        self._drop_casings = drop_casings
        self._recoil_factor = recoil_factor
        self._bullet_damage = bullet_damage
        self._bullet_size = bullet_size
        self._barrel_length = barrel_length
        self._parent_position_offset = convert_coord(
            parent_position_offset, Vec2
        )
        self._bullet_explosion_radius = bullet_explosion_radius
        self._bullet_explosion_damage = bullet_explosion_damage
        self._bullet_lifetime = bullet_lifetime
        self._sound_effect = sound_effect
        # self.__sound_effect: ContinuousSoundEffect = ...
        self._texture_id_r, _ = textures.get_texture(
            self._image_name,
            self._image_size,
            "x"
        )
        self._texture_id_l, _ = textures.get_texture(
            self._image_name,
            self._image_size
        )
        self._size = Vec2.from_cartesian(*self._image_size)
        if self._image_rotate_anchor is ...:
            self._image_rotate_anchor = self._size / 2

    @property
    def mag_size(self) -> int:
        return self.mag_size

    @property
    def recoil_factor(self) -> float:
        return self._recoil_factor

    @property
    def bullet_speed(self) -> float:
        return self._bullet_speed

    def get_mag_state(
            self,
            max_out: float
    ) -> tuple[float, int] | tuple[float, float]:
        """
        returns the current mag size (rising when reloading)
        :param max_out: output size
        :returns: x out of max_out, value of current state
        """
        if not self._current_reload_time:
            return self._mag_state * (
                    max_out / self._mag_size
            ), self._mag_state

        return (
            (
                    (
                            self._reload_time - self._current_reload_time
                    ) / self._reload_time
            ) * max_out,
            round(self._current_reload_time, 2)
        )

    def update(self, delta: float) -> None:
        """
        update weapon state (like reloading, ...)
        """
        # reload time
        if self._current_reload_time > 0:
            self._current_reload_time -= delta

        if self._current_reload_time < 0 and self._mag_state <= 0:
            self._current_reload_time = 0
            self._mag_state = self._mag_size
            sound_effect = sound_effect_wrapper("reload_generic")
            sound_effect.volume = .4
            sound_effect.play()

        # recoil time
        if self._current_recoil_time > 0:
            self._current_recoil_time -= delta

        if self._current_recoil_time < 0:
            self._current_recoil_time = 0

        # sound
        if self._current_sound_time > 0:
            self._current_sound_time -= delta

        if self._current_sound_time < 0:
            self._current_sound_time = 0

            if hasattr(self._sound_effect, "done"):
                self._sound_effect.done()

    def shoot(
            self,
            direction: Vec2,
            bullet_tof: float = ...,
            target_pos: Vec2 = ...
    ) -> bool:
        """
        shoot a bullet and check for recoil and reload

        :returns: true if shot
        """
        # check if mag is empty
        if self._mag_state <= 0:
            if self._current_reload_time == 0:
                self._current_reload_time = self._reload_time

            return False

        # audio
        if self._sound_effect is not ...:
            self._current_sound_time = self._recoil_time

        if self._current_recoil_time > 0:
            return False

        if self._sound_effect is not ...:
            if not self._sound_effect.playing:
                self._sound_effect.play()

            if hasattr(self._sound_effect, "stage_one_done"):
                if not self._sound_effect.stage_one_done:
                    return False

        # inaccuracy
        offset = randint(-255, 255) / 255
        offset *= self._inaccuracy
        direction.angle += offset
        direction.normalize()

        # recoil
        if hasattr(self.parent, "_movement_acceleration"):
            recoil = direction * self.parent._movement_acceleration
            recoil *= self._recoil_factor
            self.parent.acceleration -= recoil

        self._current_recoil_time = self._recoil_time

        self._mag_state -= 1

        # actual bullet
        if bullet_tof is ...:
            bullet_lifetime = self._bullet_lifetime

        else:
            bullet_lifetime = bullet_tof

        Bullet(
            self.parent,
            self._coalition,
            self.parent.position + self._parent_position_offset
            + direction.normalize() * self._barrel_length * .45,
            direction.normalize() * self._bullet_speed + self.parent.velocity,
            base_damage=self._bullet_damage,
            size=self._bullet_size,
            explosion_radius=self._bullet_explosion_radius,
            explosion_damage=self._bullet_explosion_damage,
            time_to_life=bullet_lifetime,
            target_pos=target_pos
        )

        if self._drop_casings:
            # casing
            casing_direction = direction.normalize()
            casing_direction.x *= -.3
            Bullet(
                self.parent,
                self._coalition,
                self.parent.position + Vec2.from_cartesian(0, 7)
                + casing_direction * self.parent.size.length * .4,
                casing_direction * 500 + self.parent.velocity,
                casing=True
            )

        return True

    def reload(self, instant: bool = False) -> None:
        """
        reload the weapon
        """
        self._current_reload_time = 0 if instant else self._reload_time

        if instant:
            self._mag_state = self._mag_size

        else:
            self._mag_state = 0

    def stop(self) -> None:
        """
        stop all running effects
        """
        if self._sound_effect is not ...:
            self._sound_effect.stop()

    def draw_at(self, position: Vec2, angle: float) -> None:
        """
        draw the weapon (centered) at a specified position
        """
        angle = angle % 360
        # offset = self._image_offset + self._parent_position_offset
        offset = self._parent_position_offset

        if self.parent.facing.x < 0:
            offset.x = -offset.x

        position += offset

        if 90 < angle < 270:
            anchor = Vec2.from_cartesian(
                self._size.x - self._image_rotate_anchor.x,
                self._image_rotate_anchor.y
            )
            renderer.draw_textured_quad(
                self._texture_id_l,
                (position - Updated.world_position - anchor).xy,
                self._size.xy,
                rotate_angle=angle - 180,
                rotate_anchor=anchor
            )

        else:
            renderer.draw_textured_quad(
                self._texture_id_r,
                (position - Updated.world_position - self._image_rotate_anchor).xy,
                self._size.xy,
                rotate_angle=angle,
                rotate_anchor=self._image_rotate_anchor
            )


class Minigun(BaseWeapon):
    _image_name: str = "minigun"
    _image_size: tuple[int, int] = (128, 64)
    # _image_offset: Vec2 = Vec2.from_cartesian(25, 1)
    _image_rotate_anchor: Vec2 = Vec2.from_cartesian(35, 30)

    def __init__(
            self,
            parent,
            drop_casings: bool = False,
            parent_position_offset: coord_t = Vec2()
    ) -> None:
        super().__init__(
            parent,
            reload_time=3,
            recoil_time=.02,
            recoil_factor=2,
            mag_size=80,
            inaccuracy=.01093606,
            bullet_speed=1600,
            bullet_damage=2,
            barrel_length=210,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            sound_effect=MinigunSound()
        )


class Ak47(BaseWeapon):
    _image_name: str = "ak47"
    _image_size: tuple[int, int] = (80, 40)
    # _image_offset: Vec2 = Vec2.from_cartesian(15, -6)
    _image_rotate_anchor: Vec2 = Vec2.from_cartesian(30, 20)

    def __init__(
            self,
            parent,
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2()
    ) -> None:
        super().__init__(
            parent,
            reload_time=2.5,
            recoil_time=.1,
            recoil_factor=8,
            mag_size=30,
            inaccuracy=0.03,
            bullet_size=11,
            bullet_speed=1200,
            bullet_damage=2.5,
            barrel_length=140,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            sound_effect=AK47Sound()
        )


class Sniper(BaseWeapon):
    _image_name: str = "sniper"
    _image_size: tuple[int, int] = (120, 60)
    # _image_offset: Vec2 = Vec2.from_cartesian(0, 25)
    _image_rotate_anchor: Vec2 = Vec2.from_cartesian(25, 33)

    def __init__(
            self,
            parent,
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2()
    ) -> None:
        s = Shotgun()
        s.volume = .7
        super().__init__(
            parent,
            reload_time=5,
            recoil_time=2,
            recoil_factor=50,
            mag_size=6,
            inaccuracy=.00500002,
            bullet_size=15,
            bullet_speed=2500,
            bullet_damage=4,
            barrel_length=230,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            sound_effect=s
        )


class Mortar(BaseWeapon):
    _bullet_image = BULLET_PATH

    def __init__(
            self,
            parent,
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2()
    ) -> None:
        super().__init__(
            parent,
            reload_time=4,
            recoil_time=0,
            recoil_factor=100,
            mag_size=1,
            inaccuracy=.00100002,
            bullet_size=22,
            bullet_speed=1400,
            bullet_damage=40,
            barrel_length=5,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_explosion_radius=200,
            bullet_explosion_damage=50,
            bullet_lifetime=7,
        )


class Flak(BaseWeapon):
    def __init__(
            self,
            parent,
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2()
    ) -> None:
        super().__init__(
            parent,
            reload_time=3,
            recoil_time=.15,
            recoil_factor=80,
            mag_size=4,
            inaccuracy=.0100002,
            bullet_size=18,
            # bullet_speed=1400*2,  # can shoot down bullets, but is too op
            bullet_speed=1400,
            bullet_damage=30,
            barrel_length=5,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_explosion_radius=100,
            bullet_explosion_damage=40,
            bullet_lifetime=5,
            sound_effect=Shotgun
        )


class CRAM(BaseWeapon):
    def __init__(
            self,
            parent,
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2()
    ) -> None:
        super().__init__(
            parent,
            reload_time=8,
            recoil_time=.005,
            recoil_factor=2,
            mag_size=800,
            inaccuracy=.001093606,
            bullet_speed=3000,
            bullet_damage=.1,
            barrel_length=20,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_size=9,
            bullet_lifetime=1,
            bullet_explosion_damage=.1,
            bullet_explosion_radius=15,
            # sound_effect=MinigunSound
        )
