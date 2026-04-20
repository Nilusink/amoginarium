"""
_player.py
26. January 2024

defines a player

Author:
Nilusink
"""
from contextlib import suppress
from time import perf_counter
from ctypes import Array
from icecream import ic
import pygame as pg
import typing as tp

from amoginarium.shared.audio import DeathSound, SoundEffect, OnHoverButtonSound
from amoginarium.shared import Coalitions, ItemLike, ItemSlot, base_entity_t
from amoginarium.shared import ProcessCommand, BaseCommandType, DummyCIDs
from amoginarium.shared.utility import Vec2, convert_coord
from amoginarium import pv

from ..graphics_dummies import Controller
from ._weapons import BaseWeapon, Minigun, HandThrownGrenade, Ak47
from ._exacto import ExactoSniper
from ._logic_groups import GravityAffected, FrictionXAffected, Updated
from ._logic_groups import CollisionDestroyed, WallCollider, Players
from ._items import Shield, HealingPotion, JetBag
from ._dynamic_entities import DYNAMIC_ENTITIES
from ._base_entity import LogicGameEntity
from ._charged_weapons import RailGun
from ._inventory import Inventory
from ._island import Island
from ._base_item import Item


PIXEL_MASK = pg.mask.Mask((1, 1), True)
PIXEL_LINE_VERTICAL = pg.mask.Mask((1, 32), True)


class Player(LogicGameEntity):
    _impulse_resistance_factor: float = 1  # 0 = completely resistant
    _heal_per_second: float = 2
    _time_to_heal: float = 5
    _max_speed: float = 1000
    _max_hp: int = 80
    __heading = 1
    _hp: float = 0

    on_wall: bool = False

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            controller: Controller,
            position: Vec2 | None = None,
            initial_velocity: Vec2 | None = None,
            size: Vec2 | None = None,
            parent: LogicGameEntity | None = None,
            coalition: Coalitions = ...,
    ) -> None:
        self._hp = self._max_hp
        self._controller = controller
        self._on_ground = False
        self._alive = True

        if not size:
            size: Vec2 = Vec2().from_cartesian(64, 64)

        if not position:
            position: Vec2 = Players.spawn_point

        if coalition is ...:
            coalition = Coalitions.blue

        self._initial_position = position.copy()
        self._death_sound = DeathSound()

        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=position,
            initial_velocity=initial_velocity,
            parent=parent,
            coalition=coalition
        )

        self._groaning = SoundEffect(("groaning", "hugh_1"))
        self._pickup_sound = OnHoverButtonSound()

        self._current_weapon = 0
        self._weapon_change_pressed = False
        self._in_inventory = False
        self._inventory_pressed = False
        self._hover_slot: ItemSlot | None = None
        self._holding_slot: ItemSlot | None = None
        self._inventory = Inventory(self, 30, self._set_slot, self._remove_hover)
        self._hotbar = Inventory(self, 10, self._set_slot, self._remove_hover)
        self._hotbar.set_highlight(0)
        items = [
            Ak47(self, self._runtime_buffer, False, parent_position_offset=(0, 0)),
            Minigun(self, self._runtime_buffer, False, parent_position_offset=(0, 10)),
            DYNAMIC_ENTITIES["weapon.sniper"](self, self._runtime_buffer, False),
            ExactoSniper(self, self._runtime_buffer, False),
            HandThrownGrenade(self, self._runtime_buffer, False),
            Shield(self._runtime_buffer, Vec2().from_cartesian(64, 0)),
            HealingPotion(self._runtime_buffer, Vec2().from_cartesian(0, 5)),
            JetBag(self._runtime_buffer, Vec2().from_cartesian(-24, 0)),
            # Bow(self, False, parent_position_offset=(0, 0)),
            RailGun(self, self._runtime_buffer, False, parent_position_offset=(0, 0)),
        ]
        for item in items:
            self._hotbar.add_item(
                item,
                1
            )

        for slot in self._hotbar:
            if slot.item:
                slot.item.hide()
                if hasattr(slot.item, "reload"):
                    slot.item.reload(True)

        self.item.show()

        self._last_hit = perf_counter()

        self.add(
            CollisionDestroyed,
            FrictionXAffected,
            GravityAffected,
            WallCollider,
            Players
        )

        # spawn graphics dummy
        pv.COQ.put(ProcessCommand(
            type=BaseCommandType.spawn_dummy,
            kwargs={
                "id": self.id,
                "cid": DummyCIDs.player.value,
                "i_id": self._inventory.id,
                "h_id": self._hotbar.id,
            },
        ))

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
    def on_ground(self) -> bool:
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
    def item(self) -> ItemLike | None:
        if not hasattr(self, "_hotbar"):
            return None

        if self._hotbar.get_count(self._current_weapon) > 0:
            return self._hotbar.get_item(self._current_weapon)

        else:
            return None

    def pickup_item(self, item: Item) -> None:
        if self._hotbar.try_add_item(item, 1) > 0:
            self._pickup_sound.play()
        
        # show item again to make sure it is visible
        if self.item:
            self.item.show()

    def next_weapon(self) -> None:
        """
        switches to the next weapon
        """
        if self.item:
            self.item.stop()
            self.item.hide()

        self._current_weapon += 1
        if self._current_weapon >= self._hotbar.num_slots:
            self._current_weapon = 0

        if self.item:
            self.item.show()

        self._hotbar.set_highlight(self._current_weapon)

    def previous_weapon(self) -> None:
        """
        switches to the previous weapon
        """
        if self.item:
            self.item.stop()
            self.item.hide()

        self._current_weapon -= 1
        if self._current_weapon < 0:
            self._current_weapon = self._hotbar.num_slots - 1

        if self.item:
            self.item.show()

        self._hotbar.set_highlight(self._current_weapon)

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
        # damage *= 0
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

    def _update(self, delta):
        # update reloads
        for hover_slot in self._hotbar:
            if hover_slot.count > 0:
                hover_slot.item.update(delta)

        acc_fac = pv.global_vars.get_acceleration_factor()
        ppm = pv.global_vars.get_pixel_per_meter()
        ssf = pv.global_vars.get_screen_size_fac()

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

        # accelerate right
        if self._controller.joy_x > 0:
            if self.velocity.x < self._max_speed:
                self.velocity.x += self._impulse_resistance_factor * delta * acc_fac * 12

            # self.facing.x = 1

        # accelerate left
        elif self._controller.joy_x < 0:
            if self.velocity.x > -self._max_speed:
                self.velocity.x -= self._impulse_resistance_factor * delta * acc_fac * 12

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

        mouse_pos = self._controller.mouse_x, self._controller.mouse_y
        vector = convert_coord(
            (
                (mouse_pos[0] / ppm) * ssf.x,
                (mouse_pos[1] / ppm) * ssf.y,
            ),
            Vec2,
        )
        vector -= self.world_position
        self.facing.angle = vector.angle

        # directional stuff
        if not self._in_inventory:
            if self._controller.shoot:
                # shot_direction = self.facing.copy()
                # shot_direction.y = -.4
                if isinstance(self.item, BaseWeapon):
                    if hasattr(self.item, "charge"):
                        self.item.charge()

                    elif self.item.shoot(self.facing):
                        self._controller.feedback_shoot()

                elif self.item:
                    self.item.use()

            else:
                if isinstance(self.item, BaseWeapon):
                    if hasattr(self.item, "charge"):
                        item: ... = self.item

                        if item.charged > 0:
                            if self.item.shoot(self.facing):
                                self._controller.feedback_shoot()

                        else:
                            self.item.stop_shooting()

                    else:
                        self.item.stop_shooting()

                elif self.item:
                    self.item.stop_use()
        #
        # else:
        #     hover_slot = self._hover_slot
        #     holding_slot = self._holding_slot
        #     if holding_slot:
        #         if self._controller.shoot:
        #             self._holding_slot.item.position.x = self._controller.mouse_x * pv.global_vars.screen_size_fac_x
        #             self._holding_slot.item.position.y = self._controller.mouse_y * pv.global_vars.screen_size_fac_y
        #
        #         else:
        #             if hover_slot:
        #                 # switch slot items
        #                 item1: VisibleItem = holding_slot.item
        #                 count1 = holding_slot.count
        #                 sid1 = holding_slot.id
        #                 parent1 = holding_slot.parent
        #
        #                 item2: VisibleItem = hover_slot.item
        #                 count2 = hover_slot.count
        #                 sid2 = hover_slot.id
        #                 parent2 = hover_slot.parent
        #
        #                 # set slots
        #                 parent1.set_slot(sid1, item2, count2)
        #                 parent2.set_slot(sid2, item1, count1)
        #
        #                 if item1:
        #                     item1.hide()
        #
        #                 self._set_slot(parent2.get_slot(sid2))
        #
        #             else:
        #                 if holding_slot.item:
        #                     holding_slot.item.hide()
        #
        #             self._holding_slot = None
        #
        #     elif hover_slot:
        #         if self._controller.shoot:
        #             if hover_slot.item:
        #                 hover_slot.item.show()
        #                 self._holding_slot = hover_slot

        # drop item
        if self._controller.drop:
            vel = self.velocity + Vec2().from_polar(
                self.facing.angle,
                300
            )
            self._hotbar.drop_item(
                self._current_weapon,
                self.position,
                vel
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
                self._set_bit("flags", 15, self._in_inventory)

        else:
            self._inventory_pressed = False

        super()._update(delta)

        if wall_rider is not ...:
            self.velocity -= wall_rider.velocity

        if self.item:
            self.item.facing.angle = self.facing.angle

        self._runtime_buffer[self.id].param0 = self._hp / self._max_hp

        if self.position.y > 2000:
            self.kill()

    def update_rect(self) -> None:
        self.rect = pg.Rect(
            self.position.x - self.size.x / 4,
            self.position.y - self.size.y / 2,
            self.size.x / 2,
            self.size.y
        )

    def kill(self, killed_by=...) -> None:
        """
        remove player from almost all groups
        """
        # set state to dead
        self._alive = False

        self._death_sound.play()
        if hasattr(self.item, "stop_use"):
            self.item.stop_use()

        elif hasattr(self.item, "stop_shooting"):
            self.item.stop_shooting()

        # remove from every group except players
        super().kill(killed_by)
        # self.add(Players)

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
            Updated,
        )

        # reset health
        self._hp = self._max_hp
        # if isinstance(self.item, BaseWeapon):
        #     self.item.reload(True)
        #
        # elif self.item:
        #     self.item.reset()

        # reset position / velocity
        self.position = self._initial_position.copy()
        ic(self.position, self._initial_position, pos)
        self._acceleration_to_add *= 0
        self.acceleration *= 0
        self.velocity *= 0

        if pos is not ...:
            self.position = pos.copy()

        super()._update(0)
