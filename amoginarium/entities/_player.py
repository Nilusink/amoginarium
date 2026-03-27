"""
_player.py
26. January 2024

defines a player

Author:
Nilusink
"""
from contextlib import suppress
from time import perf_counter
from icecream import ic
import pygame as pg
import typing as tp

from ._groups import GravityAffected, FrictionXAffected, HasBars
from ._groups import CollisionDestroyed, WallCollider, Players
from ._groups import Updated, Drawn
from ..audio import DeathSound, SoundEffect
from ._base_entity import LRImageEntity
from ._weapons import Ak47, Minigun, Sniper, Mortar, Flak, BaseWeapon, CRAM
from ._items import BaseItem, Shield, HealingPotion, JetBag, VisibleItem
from ._charged_weapon import Bow, ChargedWeapon, RailGun
from ..shared import Coalitions, WeaponLike, ItemLike, ItemSlot
from ..logic import Vec2, convert_coord, Color
from ._weapons import HandThrownGrenade
from ..render_bindings import renderer
from ..base._textures import textures
from ..controllers import Controller
from ._island import Island
from ._inventory import Inventory
from ..shared import global_vars

PLAYER_LEFT_64_PATH = "amogus64left"
PLAYER_RIGHT_64_PATH = "amogus64right"
PLAYER_OOB_RIGHT_64_PATH = "amogusOOB64right"
PLAYER_OOB_LEFT_64_PATH = "amogusOOB64left"

PIXEL_MASK = pg.mask.Mask((1, 1), True)
PIXEL_LINE_VERTICAL = pg.mask.Mask((1, 32), True)


class Player(LRImageEntity):
    _player_right_64_texture: int = ...
    _player_left_64_texture: int = ...
    _player_oob_right_1_texture: int = ...
    _player_oob_right_2_texture: int = ...
    _player_oob_left_1_texture: int = ...
    _player_oob_left_2_texture: int = ...
    _impulse_resistance_factor: float = 1  # 0 = completely resistant
    _heal_per_second: float = 2
    _time_to_heal: float = 5
    _max_speed: float = 1000
    _max_hp: int = 80
    __heading = 1
    _hp: float = 0

    on_wall: bool = False

    def __new__(cls, *args, **kwargs):
        # only load texture once
        if cls._player_left_64_texture is ...:
            cls.load_textures()

        return super(Player, cls).__new__(cls)

    @classmethod
    def load_textures(cls) -> None:
        cls._player_right_64_texture, _ = textures.get_texture(
            PLAYER_RIGHT_64_PATH,
            (64, 64)
        )
        cls._player_left_64_texture, _ = textures.get_texture(
            PLAYER_LEFT_64_PATH,
            (64, 64),
        )

        cls._player_oob_right_1_texture, _ = textures.get_texture(
            PLAYER_OOB_RIGHT_64_PATH,
            (64, 64),
            mirror="x"
        )
        cls._player_oob_right_2_texture, _ = textures.get_texture(
            PLAYER_OOB_LEFT_64_PATH,
            (64, 64),
            mirror="x"
        )
        cls._player_oob_left_1_texture, _ = textures.get_texture(
            PLAYER_OOB_RIGHT_64_PATH,
            (64, 64),
        )
        cls._player_oob_left_2_texture, _ = textures.get_texture(
            PLAYER_OOB_LEFT_64_PATH,
            (64, 64),
        )

    def __init__(
            self,
            coalition: Coalitions,
            controller: Controller,
            facing: Vec2 = ...,
            initial_position: Vec2 = ...,
            initial_velocity: Vec2 = ...,
            size: int = 64
    ) -> None:
        self._hp = self._max_hp
        self._controller = controller
        self._on_ground = False
        self._alive = True

        if initial_position is ...:
            initial_position = Players.spawn_point

        self._initial_position = initial_position.copy()

        # load textures
        if size == 64:
            self._texture_right = self._player_right_64_texture
            self._texture_left = self._player_left_64_texture

        else:
            self._texture_right, _ = textures.get_texture(
                PLAYER_RIGHT_64_PATH,
                (size, size)
            )
            self._texture_left, _ = textures.get_texture(
                PLAYER_RIGHT_64_PATH,
                (size, size),
                mirror="x"
            )
        self._image_size = size

        self._death_sound = DeathSound()

        super().__init__(
            size=Vec2().from_cartesian(size, size),
            facing=facing,
            initial_position=initial_position,
            initial_velocity=initial_velocity,
            coalition=coalition
        )

        self._groaning = SoundEffect(("groaning", "hugh_1"))


        self._current_weapon = 0
        self._weapon_change_pressed = False
        self._in_inventory = False
        self._inventory_pressed = False
        self._hover_slot: ItemSlot | None = None
        self._holding_slot: ItemSlot | None = None
        self._inventory = Inventory(
            30,
            self._set_slot,
            self._remove_hover
        )
        self._hotbar = Inventory(
            10,
            self._set_slot,
            self._remove_hover
        )
        items = [
            Ak47(self, False, parent_position_offset=(0, 0)),
            Minigun(self, False, parent_position_offset=(0, 10)),
            Sniper(self, False),
            HandThrownGrenade(self, False),
            Shield(self, Vec2().from_cartesian(50, 0)),
            HealingPotion(self, Vec2().from_cartesian(0, 5)),
            JetBag(self, Vec2().from_cartesian(-24, 0)),
            Bow(self, False, parent_position_offset=(0, 0)),
            RailGun(self, False, parent_position_offset=(0, 0)),
        ]
        for item in items:
            self._hotbar.add_item(
                VisibleItem(item),
                1
            )
        for slot in self._hotbar:
            if slot.item:
                if hasattr(slot.item.item, "reload"):
                    slot.item.item.reload(True)

        self._last_hit = perf_counter()

        self.add(
            CollisionDestroyed,
            FrictionXAffected,
            GravityAffected,
            WallCollider,
            Players,
            HasBars
        )

    def _set_slot(self, slot_id: ItemSlot) -> None:
        self._hover_slot = slot_id

    def _remove_hover(self, slot_id) -> None:
        if slot_id == self._hover_slot:
            self._hover_slot = None

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def hp(self) -> float:
        return self._hp

    @property
    def on_ground(self) -> bool | Island:
        if self._controller.joy_y < 0:
            return False

        return self._on_ground

    @property
    def alive(self) -> bool:
        """
        checks if the player is alive
        """
        return self._alive

    @property
    def item(self) -> WeaponLike | ItemLike | None:
        if not hasattr(self, "_hotbar"):
            return None

        if self._hotbar.get_count(self._current_weapon) > 0:
            return self._hotbar.get_item(self._current_weapon).item

        else:
            return None

    def pickup_item(self, item: VisibleItem) -> None:
        self._hotbar.try_add_item(item, 1)

    def next_weapon(self) -> None:
        """
        switches to the next weapon
        """
        if self.item:
            self.item.stop()

        self._current_weapon += 1
        if self._current_weapon >= self._hotbar.num_slots:
            self._current_weapon = 0

    def previous_weapon(self) -> None:
        """
        switches to the previous weapon
        """
        if self.item:
            self.item.stop()

        self._current_weapon -= 1
        if self._current_weapon < 0:
            self._current_weapon = self._hotbar.num_slots - 1

    def _item_used(self, item_id: int, used_amount: int = 1) -> bool:
        """
        remove used_amount from set item
        """
        ic(item_id, used_amount)
        with suppress(KeyError, IndexError):
            self._hotbar.use_item(self._current_weapon, used_amount)
            return self._hotbar.get_count(self._current_weapon) > 0

        return False

    def hit(self, damage: float, hit_by: tp.Self = ...) -> None:
        """
        deal damage to the player
        """
        damage = 0
        self._hp -= damage

        if damage != 0:
            self._controller.feedback_hit()

        # check for player death
        if self._hp <= 0:
            if self.item:
                self.item.stop()

            self.kill(hit_by)

        # update last hit
        self._last_hit = perf_counter()
        self._controller.feedback_heal_stop()

    def heal(self, heal: float) -> bool:
        new = self._hp + heal
        if new > self._max_hp:
            return False

        else:
            self._hp = new
            return True

    def collide_wall(self, wall: Island):
        return wall.get_collided_sides(
            (
                self.position + Vec2().from_cartesian(0, self.size.y / 2),
                PIXEL_MASK
            ),
            (
                self.position + Vec2().from_cartesian(
                    self.size.y / 2, -PIXEL_LINE_VERTICAL.get_size()[1] / 2
                ),
                PIXEL_LINE_VERTICAL
            ),
            (
                self.position - Vec2().from_cartesian(0, self.size.y / 2),
                PIXEL_MASK
            ),
            (
                self.position - Vec2().from_cartesian(
                    self.size.y / 2, PIXEL_LINE_VERTICAL.get_size()[1] / 2
                ),
                PIXEL_LINE_VERTICAL
            ),
        )

    def update(self, delta):
        # update reloads
        # self.weapon.update(delta)
        for hover_slot in self._hotbar:
            if hover_slot.count > 0:
                hover_slot.item.item.update(delta)

        # stay on ground if touching ground
        in_wall = WallCollider.collides_with(self)
        self._on_ground = False
        wall_rider: Island = ...
        if in_wall:
            wall, _ = in_wall
            wall: Island

            # check where the sprite touched the wall
            on_top, on_right, on_bottom, on_left = self.collide_wall(wall)

            # collide with walls
            self._on_ground = on_top
            if on_top and self.velocity.y >= 0:
                if self.velocity.y > 3:
                    self._controller.feedback_collide()

                if self.velocity.y > 450:
                    self._groaning.play()

                self.acceleration.y = 0
                self.velocity.y = 0
                self.position.y -= 10

                # check if +1 is over the floor
                on_top, *_ = self.collide_wall(wall)
                self.update_rect()
                if not on_top:
                    self.position.y += 10

            if on_bottom and self.velocity.y <= 0:
                if self.velocity.y < -3:
                    self._controller.feedback_collide()

                self.acceleration.y = 0
                self.velocity.y = 0
                self.position.y += 1

            if on_right and self.velocity.x >= 0:
                if self.velocity.x > 12:
                    self._controller.feedback_collide()

                self.acceleration.x = 0
                self.velocity.x = 0
                self.position.x -= 1

            if on_left and self.velocity.x <= 0:
                if self.velocity.x < -12:
                    self._controller.feedback_collide()

                self.acceleration.x = 0
                self.velocity.x = 0
                self.position.x += 1

            if self._on_ground:
                wall_rider = wall

        # update controls
        self._controller.update(delta)

        # accelerate right
        if self._controller.joy_x > 0:
            if self.velocity.x < self._max_speed:
                self.velocity.x += self._impulse_resistance_factor * delta * global_vars.acceleration_factor * 12

            # self.facing.x = 1

        # accelerate left
        elif self._controller.joy_x < 0:
            if self.velocity.x > -self._max_speed:
                self.velocity.x -= self._impulse_resistance_factor * delta * global_vars.acceleration_factor * 12

            # self.facing.x = -1

        # jump
        if self._controller.jump and self.on_ground:
            self.velocity.y = -400

        # reload
        if self._controller.reload:
            if isinstance(self.item, BaseWeapon):
                self.item.reload()

        # switch weapon
        if self._controller.wpn_f:
            if not self._weapon_change_pressed:
                self._weapon_change_pressed = True
                self.next_weapon()

        elif self._controller.wpn_b:
            if not self._weapon_change_pressed:
                self._weapon_change_pressed = True
                self.previous_weapon()

        else:
            self._weapon_change_pressed = False

        # directional stuff
        if not self._in_inventory:
            if self._controller.shoot:
                mouse_pos = pg.mouse.get_pos()
                vector = convert_coord((
                    (mouse_pos[0] / global_vars.pixel_per_meter) * global_vars.screen_size_fac_x,
                    (mouse_pos[1] / global_vars.pixel_per_meter) * global_vars.screen_size_fac_y,
                ), Vec2)
                vector -= self.world_position

                # shot_direction = self.facing.copy()
                # shot_direction.y = -.4
                if isinstance(self.item, BaseWeapon):
                    if hasattr(self.item, "charge"):
                        self.item.charge()

                    elif self.item.shoot(
                        vector
                    ):
                        self._controller.feedback_shoot()

                elif self.item:
                    self.item.use()

            else:
                if isinstance(self.item, BaseWeapon):
                    if hasattr(self.item, "charge"):
                        item: ChargedWeapon = self.item

                        if item.charged > 0:
                            mouse_pos = pg.mouse.get_pos()
                            vector = convert_coord((
                                (mouse_pos[ 0] / global_vars.pixel_per_meter) * global_vars.screen_size_fac_x,
                                (mouse_pos[1] / global_vars.pixel_per_meter) * global_vars.screen_size_fac_y,
                            ), Vec2)
                            vector -= self.world_position

                            if self.item.shoot(vector):
                                self._controller.feedback_shoot()

                        else:
                            self.item.stop_shooting()

                    else:
                        self.item.stop_shooting()

                elif self.item:
                    self.item.stop_use()

        else:
            hover_slot = self._hover_slot
            holding_slot = self._holding_slot
            if holding_slot:
                if self._controller.shoot:
                    self._holding_slot.item.position.x = self._controller.mouse_x * global_vars.screen_size_fac_x
                    self._holding_slot.item.position.y = self._controller.mouse_y * global_vars.screen_size_fac_y

                else:
                    if hover_slot:
                        # switch slot items
                        item1: VisibleItem = holding_slot.item
                        count1 = holding_slot.count
                        sid1 = holding_slot.id
                        parent1 = holding_slot.parent

                        item2: VisibleItem = hover_slot.item
                        count2 = hover_slot.count
                        sid2 = hover_slot.id
                        parent2 = hover_slot.parent

                        # set slots
                        parent1.set_slot(sid1, item2, count2)
                        parent2.set_slot(sid2, item1, count1)

                        if item1:
                            item1.hide()

                        self._set_slot(parent2.get_slot(sid2))

                    else:
                        if holding_slot.item:
                            holding_slot.item.hide()

                    self._holding_slot = None

            elif hover_slot:
                if self._controller.shoot:
                    if hover_slot.item:
                        hover_slot.item.show()
                        self._holding_slot = hover_slot

        # drop item
        if self._controller.drop:
            self._hotbar.drop_item(
                self._current_weapon,
                self.position,
                Vec2().from_cartesian(200, -200)
            )

        # heal
        if perf_counter() - self._last_hit > self._time_to_heal:
            if self._hp < self._max_hp:
                self._hp += self._heal_per_second * delta
                self._controller.feedback_heal_start()
            else:
                self._controller.feedback_heal_stop()

        # run update from parent classes
        if wall_rider is not ...:
            wall_rider.player_contact(self, delta)
            self.velocity += wall_rider.velocity

        # toggle inventory
        if self._controller.inventory:
            if not self._inventory_pressed:
                self._inventory_pressed = True
                self._in_inventory = not self._in_inventory

        else:
            self._inventory_pressed = False

        super().update(delta)

        if wall_rider is not ...:
            self.velocity -= wall_rider.velocity

        if self.position.y > 2000:
            self.kill()

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x - self.size.x / 4,
            self.position.y - self.size.y / 2,
            self.size.x / 2,
            self.size.y
        )

    def draw_at(
            self,
            pos: Vec2,
            size: Vec2,
            angle: float,
            convert_global: bool = True
    ) -> None:
        super().gl_draw(pos, size, convert_global)
        if self.item:
            self.item.draw_at(
                pos if pos is not ... else self.position,
                angle,
                size.x / self.size.x if size is not ... else 1,
                convert_global=convert_global
            )

    def gl_draw(self) -> None:
        # check if out of bounds
        # left of screen
        mouse_pos = pg.mouse.get_pos()
        vector = convert_coord((
            (mouse_pos[0] / global_vars.pixel_per_meter) * global_vars.screen_size_fac_x,
            (mouse_pos[1] / global_vars.pixel_per_meter) * global_vars.screen_size_fac_y,
        ), Vec2)
        vector -= self.world_position
        if vector.x == 0:
            self.facing.x = 1

        else:
            self.facing.x = vector.x // abs(vector.x)

        angle = vector.angle * (180 / 3.14169265358979)

        if self.world_position.x < 0:
            # facing
            if self.facing.x > 0:
                renderer.draw_textured_quad(
                    self._player_oob_left_2_texture,
                    (0, self.world_position.y),
                    (64, 64)
                )
            else:
                renderer.draw_textured_quad(
                    self._player_oob_left_1_texture,
                    (0, self.world_position.y),
                    (64, 64)
                )

        # right of screen
        elif self.world_position.x > 1920:

            # facing
            if self.facing.x > 0:
                renderer.draw_textured_quad(
                    self._player_oob_right_1_texture,
                    (1920 - 64, self.world_position.y),
                    (64, 64)
                )
            else:
                renderer.draw_textured_quad(
                    self._player_oob_right_2_texture,
                    (1920 - 64, self.world_position.y),
                    (64, 64)
                )

        else:
            if not self._in_inventory:
                self._hotbar.draw_at(
                    Vec2().from_cartesian(.5, .95),
                    .4,
                    10,
                    True,
                    self._current_weapon
                )

            else:
                # background
                renderer.draw_rounded_rect(
                    (
                            global_vars.screen_size.x * .25,
                            global_vars.screen_size.y * .1
                    ),
                    (
                        global_vars.screen_size.x * .5,
                        global_vars.screen_size.y * .8
                    ),
                    Color().from_255(80, 80, 80),
                    20,
                    False
                )

                # slots
                self._inventory.draw_at(
                    Vec2().from_cartesian(.5, .65),
                    .5,
                    10,
                    False
                )
                self._hotbar.draw_at(
                    Vec2().from_cartesian(.5, .85),
                    .5,
                    10,
                    False,
                    self._current_weapon
                )

                # character display
                renderer.draw_rounded_rect(
                    (
                            global_vars.screen_size.x * .28,
                            global_vars.screen_size.y * .17
                    ),
                    (
                        self.size.x * 3,
                        self.size.y * 4
                    ),
                    Color().from_255(50, 50, 50),
                    20,
                    False
                )
                self.draw_at(
                    Vec2().from_cartesian(
                        global_vars.screen_size.x * .28 + self.size.x * 1.5,
                        global_vars.screen_size.y * .17 + self.size.y * 2
                    ),
                    self.size * 2,
                    angle,
                    convert_global=False
                )

            self.draw_at(..., ..., angle)
            if self.item:
                self.item.draw_at(
                    self.position,
                    angle
                )

    def kill(self, killed_by=...) -> None:
        """
        remove player from almost all groups
        """
        # set state to dead
        self._alive = False

        self._death_sound.play()
        if hasattr(self.item, "kill"):
            self.item.stop_use()

        else:
            self.item.stop_shooting()

        # remove from every group except players
        super().kill(killed_by)
        self.add(Players)

    def respawn(self, pos: Vec2 = ...) -> None:
        """
        respawn the player
        """
        # update status to alive
        self._alive = True

        # re-add player to all groups
        self.add(
            CollisionDestroyed,
            FrictionXAffected,
            GravityAffected,
            WallCollider,
            Players,
            HasBars,
            Updated,
            Drawn
        )

        # reset health
        self._hp = self._max_hp
        if isinstance(self.item, BaseWeapon):
            self.item.reload(True)

        elif self.item:
            self.item.reset()

        # reset position / velocity
        self.position = self._initial_position.copy()
        self._acceleration_to_add *= 0
        self.acceleration *= 0
        self.velocity *= 0

        if pos is not ...:
            self.position = pos.copy()
