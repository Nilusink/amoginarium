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
import typing as tp
from types import EllipsisType

from amoginarium.shared import Coalitions, ItemLike, ItemSlot, base_entity_t
from amoginarium.shared import ProcessCommand, BaseCommandType, DummyCIDs
from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared.utility import Vec2, convert_coord
from amoginarium import pv

from amoginarium.shared.audio import DeathSound, SoundEffect, OnHoverButtonSound
from .._weaponry.templates import BaseWeapon
from .._weaponry import HandThrownGrenade, RailGun
from .._base import GravityAffected, FrictionXAffected, Updated
from .._base import Players, GameCollisions, CollisionType
from .._items import Shield, HealingPotion, JetBag, Inventory
from .._weaponry import ExactoSniper
from .._base import LogicGameEntity
from ...graphics_dummies import Controller
from .._dynamic_entities import DYNAMIC_ENTITIES
from .._items import Item

if tp.TYPE_CHECKING:
    from .._weaponry.templates import Bullet
    from .._world import Island


class Player(LogicGameEntity):
    _impulse_resistance_factor: float = 1  # 0 = completely resistant
    _heal_per_second: float = 2
    _time_to_heal: float = 5
    _max_speed: float = 1000
    _max_hp: int = 80
    __heading = 1
    _hp: float = 0

    on_wall: bool = False

    _DEFAULT_COLLISION_GROUP = GameCollisions.collision_group_players

    __add_position: Vec2

    __should_be_killed: int

    # noinspection PyArgumentEqualDefault
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
            coalition=coalition,
            centered=True
        )
        self._create_collision()

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
            DYNAMIC_ENTITIES["weapon.ak47"](self, self._runtime_buffer, False),
            DYNAMIC_ENTITIES["weapon.minigun"](self, self._runtime_buffer, False, parent_position_offset=(0, 10)),
            DYNAMIC_ENTITIES["weapon.sniper"](self, self._runtime_buffer, False),
            ExactoSniper(self, self._runtime_buffer, False),
            HandThrownGrenade(self, self._runtime_buffer, False),
            Shield(self._runtime_buffer, Vec2().from_cartesian(64, 0)),
            HealingPotion(self._runtime_buffer, Vec2().from_cartesian(0, 5)),
            JetBag(self._runtime_buffer, Vec2().from_cartesian(-24, 0)),
            RailGun(self, self._runtime_buffer, False, parent_position_offset=(0, 0)),
        ]
        for item in items:
            self._hotbar.add_item(
                item,
                2
            )

        for slot in self._hotbar:
            if slot.item:
                slot.item.hide()
                if hasattr(slot.item, "reload"):
                    slot.item.reload(True)

        self.item.show()

        self._last_hit = perf_counter()

        self.add(
            FrictionXAffected,
            GravityAffected,
            Players
        )

        self.__add_position = Vec2()
        self.__should_be_killed = 0

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

        if self.item:
            self.item.show()

    def next_weapon(self) -> None:
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
        ic(item_id, used_amount)
        with suppress(KeyError, IndexError):
            self._hotbar.use_item(self._current_weapon, used_amount)
            return self._hotbar.get_count(self._current_weapon) > 0
        return False

    def hit(self, damage: float, hit_by: LogicGameEntity = ...) -> None:
        self._hp -= damage

        if damage != 0:
            self._controller.feedback_hit()

        if self._hp <= 0:
            if self.item:
                self.item.stop()
            self.kill(hit_by)

        self._last_hit = perf_counter()
        self._controller.feedback_heal_stop()

    def heal(self, heal: float) -> bool:
        new = self._hp + heal
        if new > self._max_hp:
            return False
        else:
            self._hp = new
            return True

    def __on_collision_island(self, events: list[CollisionEvent["Island"]]) -> list[bool]:
        accepted_collisions: list[bool] = [False for _ in events]

        active_normals = [False, False, False, False]  # x-negative, x-positive, y-negative, y-positive
        if GameCollisions.collision_group_islands in self._active_normals.keys():
            for normal in self._active_normals[GameCollisions.collision_group_islands]:
                if normal.x < -0.5:
                    active_normals[0] = True
                elif normal.x > 0.5:
                    active_normals[1] = True
                if normal.y < -0.5:
                    active_normals[2] = True
                elif normal.y > 0.5:
                    active_normals[3] = True

        for i, event in enumerate(events):
            if abs(event.normal.x) > 0.5:
                if active_normals[0] and event.normal.x < -0.5:
                    continue
                if active_normals[1] and event.normal.x > 0.5:
                    continue
                self.__add_position *= 0
                self.__add_position.y += self.position.y - event.position.y  # try to make up for the lost y in the next update!
                self.position = event.position
                self.velocity.x = 0
                self.acceleration.x = 0
                self._controller.feedback_collide()
                accepted_collisions[i] = True
                break

            if abs(event.normal.y) > 0.5:
                if active_normals[2] and event.normal.y < -0.5:
                    continue
                if active_normals[3] and event.normal.y > 0.5:
                    continue
                self.__add_position *= 0
                self.__add_position.x += self.position.x - event.position.x  # try to make up for the lost y in the next update!
                self.position = event.position
                self.velocity.y = 0
                self.acceleration.y = 0
                if event.normal.y < -0.5:
                    if self.velocity.y > 3:
                        self._controller.feedback_collide()
                    if self.velocity.y > 450:
                        self._groaning.play()
                elif event.normal.y > 0.5:
                    if self.velocity.y < -3:
                        self._controller.feedback_collide()
                self._controller.feedback_collide()
                accepted_collisions[i] = True
                break

        return accepted_collisions

    def __on_collision_bullet(self, events: list[CollisionEvent["Bullet"]]) -> None:
        for event in events:
            dmg = event.other_entity.damage
            if dmg > 0 and event.other_entity.parent != self:
                self.hit(dmg, hit_by=event.other_entity)

    def __on_collision_item(self, events: list[CollisionEvent["Item"]]) -> None:
        for event in events:
            if event.other_entity.item_pickupable():
                self.pickup_item(event.other_entity)

    def _collision_start(
            self,
            group_id: CollisionType.GroupID,
            events: list[CollisionEvent[tp.Union["Item", "Shield", "Bullet", "Island"]]]
    ) -> list[bool] | None:
        if group_id == GameCollisions.collision_group_islands:
            events: list[CollisionEvent["Island"]]
            return self.__on_collision_island(events)
        elif group_id == GameCollisions.collision_group_bullets:
            events: list[CollisionEvent["Bullet"]]
            self.__on_collision_bullet(events)
        elif group_id == GameCollisions.collision_group_items:
            events: list[CollisionEvent["Item"]]
            self.__on_collision_item(events)
        elif group_id == GameCollisions.collision_group_shields:
            events: list[CollisionEvent["Shield"]]
            self.__on_collision_item(events)
        return None

    def _update(self, delta):
        self._on_ground = False

        if GameCollisions.collision_group_islands in self._active_normals.keys():
            for n in self._active_normals[GameCollisions.collision_group_islands]:
                if n.y < -0.5:
                    self._on_ground = True
                    if self.acceleration.y > 0:
                        self.acceleration.y = 0
                    if self.velocity.y > 0:
                        self.velocity.y = 0
                elif n.y > 0.5:
                    if self.acceleration.y < 0:
                        self.acceleration.y = 0
                    if self.velocity.y < 0:
                        self.velocity.y = 0
                if n.x < -0.5:
                    if self.acceleration.x > 0:
                        self.acceleration.x = 0
                    if self.velocity.x > 0:
                        self.velocity.x = 0
                elif n.x > 0.5:
                    if self.acceleration.x < 0:
                        self.acceleration.x = 0
                    if self.velocity.x < 0:
                        self.velocity.x = 0

        # update reloads
        for hover_slot in self._hotbar:
            if hover_slot.count > 0:
                hover_slot.item.update(delta)

        # ic(collision_manager.get_points(self._DEFAULT_COLLISION_GROUP, self.__collision_entity_id))

        acc_fac = pv.global_vars.get_acceleration_factor()
        ppm = pv.global_vars.get_pixel_per_meter()
        ssf = pv.global_vars.get_screen_size_fac()

        # accelerate right
        if self._controller.joy_x > 0:
            if self.velocity.x < self._max_speed:
                self.velocity.x += self._impulse_resistance_factor * delta * acc_fac * 12

        # accelerate left
        elif self._controller.joy_x < 0:
            if self.velocity.x > -self._max_speed:
                self.velocity.x -= self._impulse_resistance_factor * delta * acc_fac * 12

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

        # drop item
        if self._controller.drop:
            vel = self.velocity + Vec2().from_polar(
                self.facing.angle,
                300
            )
            self._hotbar.drop_item(
                self._current_weapon,
                self.position + Vec2().from_cartesian(0, self.size.y / 2),
                vel
            )

        # heal
        if perf_counter() - self._last_hit > self._time_to_heal:
            if self._hp < self._max_hp:
                self._hp += self._heal_per_second * delta
                self._controller.feedback_heal_start()
            else:
                self._controller.feedback_heal_stop()

        # toggle inventory
        if self._controller.inventory:
            if not self._inventory_pressed:
                self._inventory_pressed = True
                self._in_inventory = not self._in_inventory
                self._set_bit("flags", 15, self._in_inventory)
        else:
            self._inventory_pressed = False

        # ic(self.position, self.velocity.xy, self.acceleration.xy, self._velocity_to_add.xy, self._acceleration_to_add.xy)
        self.position += self.__add_position
        self.__add_position *= 0
        super()._update(delta)
        # ic(self.position)

        if self.item:
            self.item.facing.angle = self.facing.angle

        self._runtime_buffer[self.id].param0 = self._hp / self._max_hp

        # Only kill the player if has been below 2000 for 3 updates
        # to let the CollisionSystem check if that position is valid!
        # 3 because, because first is for any check to happen, second for restoring the y-axis-position on a wall hit
        # If you don't know what I mean by this, just ask me. But I won't know by then probably! xD
        if self.position.y > 2000:
            if self.__should_be_killed >= 2:
                self.kill()
            self.__should_be_killed += 1
        else:
            self.__should_be_killed = 0

    def _kill(self, killed_by=...) -> None:
        self._alive = False
        self._death_sound.play()

        if hasattr(self.item, "stop_use"):
            self.item.stop_use()
        elif hasattr(self.item, "stop_shooting"):
            self.item.stop_shooting()

        super()._kill(killed_by)

    def respawn(self, pos: Vec2 = ...) -> None:
        self._alive = True

        self.add(
            FrictionXAffected,
            GravityAffected,
            Players,
            Updated,
        )

        self._hp = self._max_hp
        self.position = self._initial_position.copy()

        self._acceleration_to_add *= 0
        self.acceleration *= 0
        self.velocity *= 0

        if pos is not ...:
            self.position = pos.copy()

        super()._update(0)

    def add_velocity(self, value: Vec2) -> None:
        """
        add velocity to the entity and guarantee that it will be valid (for short bursts)
        :param value: 2D velocity to add
        """
        x = value.x
        y = value.y

        if GameCollisions.collision_group_islands in self._active_normals.keys():
            for n in self._active_normals[GameCollisions.collision_group_islands]:
                dot = (x * n.x) + (y * n.y)
                if dot < 0:
                    x -= dot * n.x
                    y -= dot * n.y

        self._velocity_to_add.x += x
        self._velocity_to_add.y += y

    def add_acceleration(self, value: Vec2) -> None:
        """
        add acceleration to the entity and guarantee that it will be valid (for long accelerations)
        :param value: 2D acceleration to add
        """
        x = value.x
        y = value.y

        if GameCollisions.collision_group_islands in self._active_normals.keys():
            for n in self._active_normals[GameCollisions.collision_group_islands]:
                dot = (x * n.x) + (y * n.y)
                if dot < 0:
                    x -= dot * n.x
                    y -= dot * n.y

        self._acceleration_to_add.x += x
        self._acceleration_to_add.y += y
