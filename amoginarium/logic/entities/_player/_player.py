"""
Defines a player.

| ``Path``: amoginarium/logic/entities/_player/_player.py
| ``Project``: amoginarium
| ``Created``: 30.03.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp
from contextlib import suppress
from time import perf_counter

from icecream import ic

from amoginarium import pv
from amoginarium.shared import BaseCommandType, Coalitions
from amoginarium.shared import CurrentView, DummyCIDs, ProcessCommand
from amoginarium.shared.audio import DeathSound, OnHoverButtonSound, SoundEffect
from amoginarium.shared.utility import convert_coord, Vec2

from .._base import FrictionXAffected, GameCollisions, GravityAffected
from .._base import LogicGameEntity, Players, Updated
from .._dynamic_entities import DYNAMIC_ENTITIES
from .._items import HealingPotion, Inventory, JetBag, Shield
from .._rideables import Passenger
from .._weaponry import ExactoSniper, HandThrownGrenade, RailGun
from .._weaponry.templates import BaseWeapon

if tp.TYPE_CHECKING:
    from ctypes import Array
    from types import EllipsisType

    from amoginarium.shared import base_entity_t, ItemLike, ItemSlot, MurderViable
    from amoginarium.shared.collision_detection import CollisionEvent
    from amoginarium.shared.collision_detection import CollisionExceptionIDType
    from amoginarium.shared.collision_detection import CollisionGroupIDType

    from ...graphics_dummies import Controller
    from .._items import Item
    from .._weaponry import Grenade
    from .._weaponry.templates import Bullet, RideableTurret
    from .._world import Island


class Player(Passenger, LogicGameEntity):
    _CID = DummyCIDs.player

    _impulse_resistance_factor: float = 1  # 0 = completely resistant
    _heal_per_second: float = 2  # hp healing per second
    _time_to_heal: float = 5  # time without taking damage before healing starts
    _max_speed: float = 1000  # player maximum velocity
    _max_hp: int = 80  # player max hp
    _hp: float = 0

    on_wall: bool = False

    _DEFAULT_COLLISION_GROUP = GameCollisions.collision_group_players

    __add_position: Vec2

    __should_be_killed: int

    _bullets_do_not_initially_hit_player: CollisionExceptionIDType

    _ADVANCED_DEBUGGING = False
    _AD_VARS: tp.ClassVar[list[tuple[str, type | tuple[type, int]]]] = [
        ("_hp", float),
        ("on_ground", bool),
        ("velocity", Vec2),
        ("acceleration", Vec2)
    ]
    _AD_CONSOLE_LINES = 8

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

        self._bullets_do_not_initially_hit_player = GameCollisions.add_exception()

        if not size:
            size: Vec2 = Vec2().from_cartesian(63.9, 63.9)

        if not position:
            position: Vec2 = Players.spawn_point

        if coalition is ...:
            coalition = Coalitions.blue

        self._initial_position = position.copy()
        self._death_sound = DeathSound()
        self._colliding_rideables = []

        super().__init__(
            runtime_buffer=runtime_buffer,
            size=size,
            position=position,
            initial_velocity=initial_velocity,
            parent=parent,
            coalition=coalition,
            centered=True,
            tags=["player"],
        )
        self._create_collision()

        self._collision_exception_ids.append(self._bullets_do_not_initially_hit_player)

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
            DYNAMIC_ENTITIES["weapon.tv_guided"](self, self._runtime_buffer, False),
            DYNAMIC_ENTITIES["weapon.minigun"](
                self, self._runtime_buffer, False, parent_position_offset=(0, 10)
            ),
            DYNAMIC_ENTITIES["weapon.sniper"](self, self._runtime_buffer, False),
            ExactoSniper(self, self._runtime_buffer, False),
            HandThrownGrenade(self, self._runtime_buffer, False),
            Shield(self._runtime_buffer, Vec2().from_cartesian(64, 0)),
            HealingPotion(self._runtime_buffer, Vec2().from_cartesian(0, 5)),
            JetBag(self._runtime_buffer, Vec2().from_cartesian(-24, 0)),
            RailGun(self, self._runtime_buffer, False, parent_position_offset=(0, 0)),
            DYNAMIC_ENTITIES["weapon.rpg"](self, self._runtime_buffer, False),
        ]
        for item in items:
            self._hotbar.add_item(item, 2)

        for slot in self._hotbar:
            if slot.item:
                slot.item.hide()
                if hasattr(slot.item, "reload"):
                    slot.item.reload(instant=True)

        self.item.show()

        self._last_hit = perf_counter()

        self.add(FrictionXAffected, GravityAffected, Players)

        self.__add_position = Vec2()
        self.__should_be_killed = 0

        self.__ride_pressed = False

        self._spawn_graphics_entity(i_id=self._inventory.id, h_id=self._hotbar.id)

    def _set_slot(self, slot_id: ItemSlot) -> None:
        self._hover_slot = slot_id

    def _remove_hover(self, slot_id) -> None:
        if slot_id == self._hover_slot:
            self._hover_slot = None

    # region properties
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
    def can_pickup_item(self) -> bool:
        return True

    @property
    def item(self) -> ItemLike | None:
        if not hasattr(self, "_hotbar"):
            return None

        if self._hotbar.get_count(self._current_weapon) > 0:
            return self._hotbar.get_item(self._current_weapon)
        return None

    @property
    def controller(self) -> Controller:
        return self._controller

    # endregion

    def get_current_view(self) -> CurrentView:
        """Get current player viewport."""
        pos = self.position
        zoom = 0

        e = self.controlled_entity
        centered = False

        if e:
            cam_pos = e.get_camera_position()
            cam_zoom = e.get_camera_zoom()
            centered = e.camera_centered

            if cam_pos is not None:
                pos = cam_pos

            if cam_zoom is not None:
                zoom = cam_zoom

        return CurrentView(pos, zoom, centered=centered)

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
            self.kill(killed_by=hit_by)

        self._last_hit = perf_counter()
        self._controller.feedback_heal_stop()

    def heal(self, heal: float) -> bool:
        new = self._hp + heal
        if new > self._max_hp:
            return False
        self._hp = new
        return True

    def __collision_island(self, events: list[CollisionEvent[Island]]) -> list[bool]:
        """
        Player collision reaction to islands.
        Guarantees that the player won't get stuck
        in walls or fly through them and can still move along them.
        :param events: All details regarding the collisions
        :return: Which collisions were accepted.
        """
        accepted_collisions: list[bool] = [False for _ in events]

        active_normals = [
            False,
            False,  # x-negative, x-positive
            False,
            False,
        ]  # y-negative, y-positive
        if GameCollisions.collision_group_islands in self._active_normals:
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
                # try to make up for the lost y movement in the next update!
                self.__add_position.y += self.position.y - event.position.y
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
                # try to make up for the lost x movement in the next update!
                self.__add_position.x += self.position.x - event.position.x
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

    def __on_collision_bullet(self, events: list[CollisionEvent[Bullet]]) -> None:
        for event in events:
            dmg = event.other_entity.damage
            if dmg > 0 and event.other_entity.parent != self:
                self.hit(dmg, hit_by=event.other_entity)

    def __on_collision_item(self, events: list[CollisionEvent[Item]]) -> None:
        for event in events:
            if event.other_entity.item_pickupable():
                self.pickup_item(event.other_entity)

    def __collision_rideable_start(
        self, events: list[CollisionEvent[RideableTurret]]
    ) -> None:
        for event in events:
            event.other_entity.highlight()
            self._colliding_rideables.append(event.other_entity)

    def __collision_rideable_end(
        self, events: list[CollisionEvent[RideableTurret]]
    ) -> None:
        for event in events:
            if event.other_entity in self._colliding_rideables:
                event.other_entity.stop_highlight()
                self._colliding_rideables.remove(event.other_entity)

    @tp.override
    def _collision_start(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[Bullet | Island | Item | RideableTurret]],
    ) -> list[bool] | None:
        if group_id == GameCollisions.collision_group_islands:
            events: list[CollisionEvent[Island]]
            return self.__on_collision_island(events)

        if group_id == GameCollisions.collision_group_bullets:
            events: list[CollisionEvent[Bullet]]
            self.__on_collision_bullet(events)

        elif (
            group_id == GameCollisions.collision_group_items
            or group_id == GameCollisions.collision_group_shields
        ):
            events: list[CollisionEvent[Item]]
            self.__on_collision_item(events)

        return None

    def _collision_start(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[Item | Shield | Bullet | Island | Grenade]],
    ) -> list[bool] | None:
        """
        Distribute collision start events to different methods.

        - Island: Player walks on islands / collides with them
        - Items: Item decides if it can be picked up and calls pickup_item if so
        - Shield: Same goes for shield except is even more complex
        - Grenades: No reaction to Grenades for the player
        - Bullets: The bullet calls hit to avoid hitting too much when tunneling
        - AerodynamicEntity: The entity calls hit
            to avoid hitting too much when tunneling
        - RideableTurret: Player can enter/ride the turret.

        :param group_id: ID of the other group involved in the collision
        :param events: All details regarding the collision
        :return: List of booleans stating whether each collision is accepted.
        """
        if group_id == GameCollisions.collision_group_islands:
            events: list[CollisionEvent[Island]]
            return self.__collision_island(events)
        if (
            group_id == GameCollisions.collision_group_rideable_turrets
            or group_id == GameCollisions.collision_group_vehicles
        ):
            events: list[CollisionEvent[RideableTurret]]
            self.__collision_rideable_start(events)
            return None
        return None

    @tp.override
    def _collision_end(
        self,
        group_id: CollisionGroupIDType,
        events: list[CollisionEvent[RideableTurret]],
    ) -> None:
        if group_id == GameCollisions.collision_group_rideable_turrets:
            events: list[CollisionEvent[RideableTurret]]
            self.__collision_rideable_end(events)

    def get_initial_root_collision_exception(self) -> CollisionExceptionIDType:
        return self._bullets_do_not_initially_hit_player

    def clear_controlled_entity(self, to_clear) -> bool:
        self.__ride_pressed = True
        super().clear_controlled_entity(to_clear)

    # noinspection DuplicatedCode
    @tp.override
    def _update(self, delta) -> None:
        # update passenger status
        self.update_passenger(delta)

        # update reloads
        for hover_slot in self._hotbar:
            if hover_slot.count > 0:
                hover_slot.item.update(delta)

        acc_fac = pv.global_vars.get_acceleration_factor()
        ppm = pv.global_vars.get_pixel_per_meter()
        ssf = pv.global_vars.get_screen_size_fac()

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

        if not self.is_controlled:  # noqa: PLR1702
            if (
                len(self._colliding_rideables) > 0
                and self._controller.ride
                and not self.__ride_pressed
            ):
                self._colliding_rideables[0].set_passenger(self)

            self.__ride_pressed = self._controller.ride

            # accelerate right
            if self._controller.joy_x > 0:
                if self.velocity.x < self._max_speed:
                    self.velocity.x += (
                        self._impulse_resistance_factor * delta * acc_fac * 12
                    )

            # accelerate left
            elif self._controller.joy_x < 0:
                if self.velocity.x > -self._max_speed:
                    self.velocity.x -= (
                        self._impulse_resistance_factor * delta * acc_fac * 12
                    )

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
                    if isinstance(self.item, BaseWeapon):
                        if hasattr(self.item, "charge"):
                            self.item.charge()

                        elif self.item.shoot(self.facing):
                            self._controller.feedback_shoot()

                    elif self.item:
                        self.item.use()

                elif isinstance(self.item, BaseWeapon):
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
                vel = self.velocity + Vec2().from_polar(self.facing.angle, 300)
                self._hotbar.drop_item(
                    self._current_weapon,
                    self.position + Vec2().from_cartesian(0, self.size.y / 2),
                    vel,
                )

        # auto reload
        if isinstance(self.item, BaseWeapon):
            if self.item.get_mag_state(1)[0] == 0:
                self.item.reload()

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

        # set ridden entity properties
        ridden_pos = None
        e = self.controlled_entity
        if e:
            ridden_pos = e.get_passenger_position()

            if e.passenger_visible:
                self._collision_active = True
                self.show()

                if self.item:
                    self.item.show()

            else:
                self._collision_active = False
                self.hide()

                if self.item:
                    self.item.hide()

        else:
            self._collision_active = True
            self.show()

            if self.item:
                self.item.show()

        self._on_ground = False

        if GameCollisions.collision_group_islands in self._active_normals:
            for n in self._active_normals[GameCollisions.collision_group_islands]:
                if n.y < -0.5:
                    self._on_ground = True
                    if self.acceleration.y > 0:
                        self.acceleration.y = 0
                    if self._acceleration_to_add.y > 0:
                        self._acceleration_to_add.y = 0
                    if self.velocity.y > 0:
                        self.velocity.y = 0
                    if self._velocity_to_add.y > 0:
                        self._velocity_to_add.y = 0
                elif n.y > 0.5:
                    if self.acceleration.y < 0:
                        self.acceleration.y = 0
                    if self._acceleration_to_add.y < 0:
                        self._acceleration_to_add.y = 0
                    if self.velocity.y < 0:
                        self.velocity.y = 0
                    if self._velocity_to_add.y < 0:
                        self._velocity_to_add.y = 0
                if n.x < -0.5:
                    if self.acceleration.x > 0:
                        self.acceleration.x = 0
                    if self._acceleration_to_add.x > 0:
                        self._acceleration_to_add.x = 0
                    if self.velocity.x > 0:
                        self.velocity.x = 0
                    if self._velocity_to_add.x > 0:
                        self._velocity_to_add.x = 0
                elif n.x > 0.5:
                    if self.acceleration.x < 0:
                        self.acceleration.x = 0
                    if self._acceleration_to_add.x < 0:
                        self._acceleration_to_add.x = 0
                    if self.velocity.x < 0:
                        self.velocity.x = 0
                    if self._velocity_to_add.x < 0:
                        self._velocity_to_add.x = 0

        if ridden_pos:
            self.position = ridden_pos
            self.velocity *= 0
            self.acceleration *= 0

        else:
            self.position += self.__add_position
            self.__add_position *= 0

        super()._update(delta)

        if self.item:
            self.item.facing.angle = self.facing.angle

        self._runtime_buffer[self.id].param0 = self._hp / self._max_hp

        # Only kill the player if has been below 2000 for 3 updates
        # to let the CollisionSystem check if that position is valid!
        # 3 because, because first is for any check to happen, second for restoring the y-axis-position on a wall hit
        # If you don't know what I mean by this, just ask me. But I won't know by then probably! xD
        # if self.position.y > 2000:
        #     if self.__should_be_killed >= 2:
        #         self.kill()
        #     self.__should_be_killed += 1
        # else:
        #     self.__should_be_killed = 0

    @tp.override
    def _kill(
        self,
        killed_by: MurderViable | EllipsisType = ...,
        kill_children: bool = True,
    ) -> None:
        self._alive = False
        self._death_sound.play()

        if hasattr(self.item, "stop_use"):
            self.item.stop_use()
        elif hasattr(self.item, "stop_shooting"):
            self.item.stop_shooting()

        super()._kill(killed_by=killed_by, kill_children=kill_children)

    def respawn(self, pos: Vec2 | EllipsisType = ...) -> None:
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

    @tp.override
    def add_velocity(self, value: Vec2) -> None:
        """
        Add velocity to the entity and guarantee that it will be valid (for short bursts)
        :param value: 2D velocity to add.
        """
        x = value.x
        y = value.y

        if GameCollisions.collision_group_islands in self._active_normals:
            for n in self._active_normals[GameCollisions.collision_group_islands]:
                dot = (x * n.x) + (y * n.y)
                if dot < 0:
                    x -= dot * n.x
                    y -= dot * n.y

        self._velocity_to_add.x += x
        self._velocity_to_add.y += y

    @tp.override
    def add_acceleration(self, value: Vec2) -> None:
        """
        Add acceleration to the entity and guarantee that it will be valid (for long accelerations)
        :param value: 2D acceleration to add.
        """
        x = value.x
        y = value.y

        if GameCollisions.collision_group_islands in self._active_normals:
            for n in self._active_normals[GameCollisions.collision_group_islands]:
                dot = (x * n.x) + (y * n.y)
                if dot < 0:
                    x -= dot * n.x
                    y -= dot * n.y

        self._acceleration_to_add.x += x
        self._acceleration_to_add.y += y
