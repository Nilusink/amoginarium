"""
_weapons.py
26. January 2024

minigun go brrrrrt

Author:
Nilusink
"""
from time import perf_counter
from random import randint
from icecream import ic
import typing as tp
import numpy as np

from ._groups import GravityAffected, CollisionDestroyed, Bullets, Updated, Drawn, \
    WallBouncer
from ..audio import PresetEffect, LargeExplosion, Shotgun, sound_effect_wrapper
from ..audio import ContinuousSoundEffect, Mortar as MortarSound
from ..audio import Minigun as MinigunSound, AK47 as AK47Sound
from ..audio import CRAM as CRAMSound
from ..debugging import run_with_debug, timeit
from ..logic import Vec2, Color, convert_coord, coord_t
from ._base_entity import ImageEntity, GameEntity
from ..render_bindings import renderer
from ..shared import global_vars
from ..base._textures import textures
from ..animations import explosion
from ._groups import WallCollider

BULLET_PATH = "bullet"


class Bullet(ImageEntity):
    _bullet_image: str = (BULLET_PATH, "x")
    _casing_image: str = (BULLET_PATH, "x")
    _image_size: tuple[int, int] = ...
    _base_damage: float = 1
    _hp: int = -1

    def __new__(cls, *args, **kwargs) -> "Bullet":
        return super(Bullet, cls).__new__(cls)

    def __init__(
            self,
            parent: GameEntity,
            coalition: tp.Any,
            initial_position: Vec2,
            initial_velocity: Vec2,
            base_damage: float = 1,
            casing: bool = False,
            time_to_life: float = 2,
            explosion_radius: float = -1,
            explosion_damage: float = 0,
            target_pos: Vec2 = ...,
            size: Vec2 | int = 10,
            no_gravity=False,
            visibility_offset: float = 0
    ) -> None:
        if not isinstance(size, Vec2):
            size = Vec2.from_cartesian(size, size)

        self._casing = casing
        self._base_damage = base_damage
        self._ttl = time_to_life
        self._initial_velocity = initial_velocity
        self._explosion_radius = explosion_radius
        self._explosion_damage = explosion_damage
        self._target_pos = target_pos
        self._visibility_offset = visibility_offset

        self._start_time = perf_counter()

        # load textures
        # isize = size.xy if self._image_size is ... else self._image_size
        isize = size.xy
        self._bullet_texture, _ = textures.get_texture(
            self._bullet_image[0],
            isize,
            self._bullet_image[1]
        )
        self._casing_texture, _ = textures.get_texture(
            self._casing_image[0],
            isize,
            self._casing_image[1]
        )
        texture_id = self._bullet_texture

        super().__init__(
            texture_id=texture_id,
            size=size,
            initial_position=initial_position.copy(),
            initial_velocity=initial_velocity.copy(),
            coalition=coalition,
            parent=parent
        )

        self.remove(Updated)
        if not no_gravity:
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

        return damage

    @property
    def is_bullet(self) -> bool:
        return True

    def hit(self, _damage: float, hit_by: tp.Self = ...) -> None:
        if self._hp <= 0 or not issubclass(hit_by.__class__, Bullet):
            self.kill(killed_by=hit_by)

        else:
            self._hp -= _damage
            if self._hp <= 0:
                self.kill(killed_by=hit_by)

    def hit_someone(self, target_hp: float) -> None:
        self.kill()

    def update(self, delta):
        self._ttl -= delta
        self._visibility_offset -= delta

        if any([
            self.position.y > 2000,
            self.position.x < Updated.world_position.x - 2000,
            self.position.x > Updated.world_position.x + 4000,
            self._ttl <= 0,
            self.on_ground
        ]):
            if self.kill():
                return

        # double gravity (because why not)
        self.acceleration.y *= 2

        super().update(delta)

    # @timeit(10)
    def kill(self, killed_by: tp.Self = ...) -> bool:
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
            return True

        # explode
        if self._explosion_radius > 0:
            for d, entity in CollisionDestroyed.get_entities_in_circle(
                    self.position,
                    self._explosion_radius
            ):
                if all([
                    entity != self,
                    not issubclass(killed_by.__class__, Bullet)
                ]):
                    entity.hit(
                        (1 - .8 * d / self._explosion_radius)
                        * self._explosion_damage,
                        hit_by=self
                    )
                    if hasattr(entity, "_movement_acceleration"):
                        delta = entity.position - self.position
                        delta = delta.normalize() \
                                * entity._movement_acceleration \
                                * (
                                        1 - max(d, 40)
                                        / (self._explosion_radius * 4)
                                ) * (self._explosion_damage / 100)
                        entity.acceleration += delta

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
        return True

    def gl_draw(self) -> None:
        if self._visibility_offset > 0:
            return

        if not self._casing:
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

            if self._bullet_texture is ...:
                renderer.draw_circle(
                    self.world_position,
                    self.size.x * .5,
                    8,
                    Color.from_255(255, 255, 60)
                )
                return

            # draw image if given
            self._texture_id = self._bullet_texture

        else:
            self._texture_id = self._casing_texture

        return super().gl_draw()


class MortarShell(Bullet):
    _bullet_image: str = ("mortar_shell", "")
    _hp = .5

    def __init__(
            self,
            parent: GameEntity,
            coalition: tp.Any,
            initial_position: Vec2,
            initial_velocity: Vec2,
            base_damage: float = 40,
            casing: bool = False,
            time_to_life: float = 10,
            explosion_radius: float = 200,
            explosion_damage: float = 50,
            target_pos: Vec2 = ...,
            size=Vec2.from_cartesian(40, 20),
            no_gravity=False,
            **kwargs
    ) -> None:
        super().__init__(
            parent,
            coalition,
            initial_position,
            initial_velocity,
            base_damage,
            casing,
            time_to_life,
            explosion_radius,
            explosion_damage,
            target_pos,
            size,
            no_gravity,
            **kwargs
        )


class Grenade(Bullet):
    _bullet_image: str = ("grenade", "")
    _hp = .05
    _bounce_friction = .7

    def __init__(
            self,
            parent: GameEntity,
            coalition: tp.Any,
            initial_position: Vec2,
            initial_velocity: Vec2,
            base_damage: float = 0,
            casing: bool = False,
            time_to_life: float = 5,
            explosion_radius: float = 150,
            explosion_damage: float = 50,
            target_pos: Vec2 = ...,
            size=20,
            no_gravity=False,
            **kwargs
    ) -> None:
        super().__init__(
            parent,
            coalition,
            initial_position,
            initial_velocity,
            base_damage,
            casing,
            time_to_life,
            explosion_radius,
            explosion_damage,
            target_pos,
            size,
            no_gravity,
            **kwargs
        )

        self.in_wall = None
        self.add(WallBouncer)

    def update(self, delta):
        if self.in_wall is not None:
            pi4 = np.pi / 4
            if 7 * pi4 <= self.in_wall.angle or self.in_wall.angle < pi4:
                self.acceleration.y = 0

        super().update(delta)

    def kill(self, killed_by=...):
        # can only be killed by bullets and ttl
        if killed_by is not ...:
            if issubclass(killed_by.__class__, Bullet):
                self._ttl = 0

        if self._ttl > 0:
            return False

        return super().kill(killed_by)


class BaseWeapon:
    _image_name: str = "amogus64right"
    _image_size: tuple[int, int] = (16, 16)
    _image_mirror: bool = False
    _image_offset: Vec2 = Vec2.from_cartesian(0, 15)
    _no_bullet_gravity: bool = False
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
            bullet_size: Vec2 | int = 10,
            bullet_damage: float = 1,
            bullet_explosion_radius: float = -1,
            bullet_explosion_damage: float = 0,
            drop_casings: bool = False,
            bullet_lifetime=4,
            sound_effect: ContinuousSoundEffect | PresetEffect = ...,
            bullet_type: tp.Type[Bullet] = Bullet,
            bullet_visibility_offset: float = 0  # time offset
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
        self._bullet_type = bullet_type
        self._bullet_visibility_offset = bullet_visibility_offset
        # self.__sound_effect: ContinuousSoundEffect = ...
        self._texture_id_r, _ = textures.get_texture(
            self._image_name,
            self._image_size,
            "" if self._image_mirror else "x"
        )
        self._texture_id_l, _ = textures.get_texture(
            self._image_name,
            self._image_size,
            "x" if self._image_mirror else ""
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

    @property
    def parent_position_offset(self) -> Vec2:
        return self._parent_position_offset.copy()

    @property
    def barrel_length(self) -> float:
        return self._barrel_length

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

        # if self._current_sound_time < 0:
        #     self._current_sound_time = 0

    def stop_shooting(self):
        if hasattr(self._sound_effect, "done"):
            if self._sound_effect.playing:
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
                self.stop_shooting()

            return False

        # audio
        if self._sound_effect is not ...:
            self._current_sound_time = self._recoil_time

        if self._current_recoil_time > 0:
            return False

        if self._sound_effect is not ...:
            if not self._sound_effect.playing:
                self._sound_effect.play()

            elif not hasattr(self._sound_effect, "stage_one_done"):
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

        self._bullet_type(
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
            target_pos=target_pos,
            no_gravity=self._no_bullet_gravity,
            visibility_offset=self._bullet_visibility_offset
        )

        if self._drop_casings:
            # casing
            casing_direction = direction.normalize()
            casing_direction.x *= -.3
            self._bullet_type(
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
        if hasattr(self._sound_effect, "done"):
            if 0 < self._sound_effect.playing < 3:
                self._sound_effect.done()

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
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            sound_effect=MinigunSound(),
            bullet_visibility_offset=.058
        )


class Ak47(BaseWeapon):
    _image_name: str = "ak47"
    _image_size: tuple[int, int] = (80, 40)
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
            bullet_speed=1250,
            bullet_damage=2.5,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            sound_effect=AK47Sound(),
            bullet_visibility_offset=.043
        )


class Sniper(BaseWeapon):
    _image_name: str = "sniper"
    _image_size: tuple[int, int] = (120, 60)
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
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            sound_effect=s,
            bullet_visibility_offset=.04
        )


class Mortar(BaseWeapon):
    _bullet_image = BULLET_PATH
    _image_name: str = "mortar"
    _image_size: tuple[int, int] = (25 * 1.5, 17 * 1.5)
    _image_rotate_anchor: Vec2 = Vec2.from_cartesian(7.5 * 1.5, 8 * 1.5)

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
            bullet_size=Vec2.from_cartesian(40, 20),
            bullet_speed=1400,
            bullet_damage=40,
            barrel_length=10,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_explosion_radius=200,
            bullet_explosion_damage=50,
            bullet_lifetime=7,
            sound_effect=MortarSound(),
            bullet_type=MortarShell,
            bullet_visibility_offset=.025
        )


class Flak(BaseWeapon):
    _image_name: str = "FLAK_canon"
    _image_size: tuple[int, int] = (256, 128)
    _image_rotate_anchor: Vec2 = Vec2.from_cartesian(83, 59)

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
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_explosion_radius=100,
            bullet_explosion_damage=40,
            bullet_lifetime=5,
            sound_effect=Shotgun().set_volume(.8),
            bullet_visibility_offset=.13
        )


class CRAM(BaseWeapon):
    _image_name: str = "CRAM_canon"
    _image_mirror = True
    _image_size: tuple[int, int] = (128, 128)
    _image_rotate_anchor: Vec2 = Vec2.from_cartesian(32, 79)

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
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_size=9,
            bullet_lifetime=1,
            bullet_explosion_damage=.1,
            bullet_explosion_radius=15,
            sound_effect=CRAMSound(),
            bullet_visibility_offset=.027
        )


class HandThrownGrenade(BaseWeapon):
    _image_name: str = "grenade"
    _image_mirror = True
    _image_size: tuple[int, int] = (32, 32)
    _image_rotate_anchor: Vec2 = Vec2.from_cartesian(16, 16)

    def __init__(
            self,
            parent,
            drop_casings: bool = False,
            parent_position_offset: Vec2 | tuple[float, float] = Vec2()
    ) -> None:
        super().__init__(
            parent,
            reload_time=5,
            recoil_time=2,
            recoil_factor=2,
            mag_size=1,
            inaccuracy=.01,
            bullet_speed=800,
            bullet_damage=0,
            barrel_length=0,
            parent_position_offset=parent_position_offset,
            drop_casings=drop_casings,
            bullet_size=32,
            bullet_lifetime=5,
            bullet_explosion_damage=50,
            bullet_explosion_radius=150,
            # sound_effect=CRAMSound(),
            bullet_visibility_offset=.0,
            bullet_type=Grenade
        )
