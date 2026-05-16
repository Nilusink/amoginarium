"""
amoginarium/logic/entities/_items/_shield.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from types import EllipsisType
from ctypes import Array
import typing as tp

from amoginarium.shared.collision_detection import CollisionEvent
from amoginarium.shared.utility import Vec2
from amoginarium.shared import base_entity_t, ItemCIDs
from .. import Updated

from amoginarium.shared.audio import MetalPings, RandomizedEffect
from .._base import LogicGameEntity, GameCollisions, CollisionType
from ._something import Something

if tp.TYPE_CHECKING:
    from .._weaponry.templates import Bullet
    from .._weaponry import Grenade
    from .._player import Player
    from .._world import Island


class Shield(Something):
    _CID = ItemCIDs.shield

    _image_name: tp.ClassVar[tuple[str, str] | str] = ("Shield_6", "4")
    _image_size: tp.ClassVar[tuple[int, int]] = (45, 80)
    _max_uses: tp.ClassVar[int] = 200  # acts as HP for shield

    _DEFAULT_COLLISION_GROUP = GameCollisions.collision_group_shields

    __slots__ = ("_in_use", "_sound")

    _in_use: bool
    _sound: RandomizedEffect

    def __init__(
            self,
            runtime_buffer: Array[base_entity_t],
            parent_position_offset: Vec2
    ) -> None:
        super().__init__(
            runtime_buffer,
            Vec2().from_cartesian(*self._image_size),
            parent_position_offset,
        )
        self._create_collision()
        # self._generate_collision_mask()

        self._sound = MetalPings().set_volume(.4, .5)
        self._in_use = False
        # self._update_mask()

        self.add(Updated)

    @property
    def hp(self) -> float:
        """hit points"""
        return self._uses_left

    @property
    def in_use(self) -> bool:
        return self._in_use

    def use(self) -> None:
        """
        start using the item
        """
        if not self._in_use:
            self._collision_active = True
            self._in_use = True
            self.add(Updated)
            # self.add(CollisionDestroyed)

    def stop_use(self) -> None:
        """
        stop using the item
        """
        if self._in_use:
            self._collision_active = False
            self._in_use = False
            self.remove(Updated)
            # self.remove(CollisionDestroyed)

    def remove_parent(self, at_pos: Vec2, velocity: Vec2 | EllipsisType = ...) -> None:
        super().remove_parent(at_pos - Vec2().from_cartesian(self._image_size[0] * .45, self._image_size[1] * .7), velocity)

    def _collision_start(self, events: list[CollisionEvent[tp.Union["Island", "Bullet", "Grenade", "Player"]]]) -> None:
        """
        Reaction to collision
        :param events: Event details
        """
        group_id: CollisionType.GroupID = events[0].group_id
        if group_id == GameCollisions.collision_group_islands:
            self.position = events[0].position - self.size / 2
        elif group_id in (GameCollisions.collision_group_bullets, GameCollisions.collision_group_grenades):
            for event in events:
                self.hit_by_bullet(event.other_entity.damage, event.other_entity)

    def _update_collision(
            self,
            *,
            position: Vec2 | EllipsisType = ...,
            size: Vec2 | EllipsisType = ...,
            rotation: float = 0.0,
            positions: list[Vec2] | None = None,
            centered: bool | EllipsisType = ...,
            shift_history: bool = True
    ) -> None:
        super()._update_collision(
            position=self.position + self.size / 2,
            size=size,
            rotation=self.facing.angle,
            positions=positions,
            centered=True,
            shift_history=shift_history
        )

    def item_pickupable(self) -> bool:
        return self._parent is None and super().item_pickupable()

    def hit_by_bullet(self, damage: float, hit_by: LogicGameEntity | EllipsisType = ...) -> None:
        if not self._in_use:
            return

        if hit_by is not ...:
            if hit_by._tags.__contains__("bullet"):
                self._sound.play(pos=self.position)

        self._uses_left -= damage

        if self._uses_left <= 0:
            self.kill(hit_by)

    def _kill(self, killed_by: LogicGameEntity | EllipsisType = ...) -> None:
        super()._kill(killed_by)

    def _update(self, delta: float, **_) -> None:
        if self.parent:
            d = Vec2().from_polar(
                self.facing.angle, self._parent_position_offset.length
            )
            if self._in_use:
                self.size.xy = self._image_size
                self.position = self.parent.position + d - self.size / 2

            else:
                self.size.xy = self._image_size[0] * .1, self._image_size[1] * .3
                self.position = self.parent.position

            self.velocity *= 0
            self.acceleration *= 0
            self._velocity_to_add *= 0
            self._acceleration_to_add *= 0

            super()._update(delta, keep_position=True)
            return

        else:
            self.size.xy = self._image_size

        super()._update(delta)
