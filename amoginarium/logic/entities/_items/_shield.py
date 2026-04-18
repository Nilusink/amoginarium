"""
amoginarium/logic/entities/_items/_shield.py

Project: amoginarium
Created: 18.04.2026
Authors: LukasKrah
"""

from types import EllipsisType
from ctypes import Array
import typing as tp

from amoginarium.shared.utility import Vec2
from amoginarium.shared import base_entity_t, ItemCIDs

from ...audio import MetalPings, RandomizedEffect
from .._base_entities import LogicGameEntity
from ._base_item import BaseItem

# todo - collision

class Shield(BaseItem):
    _cid = ItemCIDs.shield

    _image_name: tp.ClassVar[tuple[str, str] | str] = ("Shield_6", "4")
    _image_size: tp.ClassVar[tuple[int, int]] = (45, 80)
    _max_uses: tp.ClassVar[int] = 200  # acts as HP for shield

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
        # self._generate_collision_mask()

        self._sound = MetalPings().set_volume(.4, .5)
        self._in_use = False
        # self._update_mask()

    @property
    def hp(self) -> float:
        """hit points"""
        return self._uses_left

    def use(self) -> None:
        """
        start using the item
        """
        if not self._in_use:
            self._in_use = True
            # self.add(CollisionDestroyed)

    def stop_use(self) -> None:
        """
        stop using the item
        """
        if self._in_use:
            self._in_use = False
            # self.remove(CollisionDestroyed)

    # def _update_mask(self) -> None:
        # angle = self.facing.angle * 180 / m.pi
        # angle = angle % 360
        #
        # if 90 < angle < 270:
        #     surf = pg.transform.rotate(
        #         self._mask_left_surf,
        #         -(angle - 180)
        #     )
        #
        # else:
        #     surf = pg.transform.rotate(
        #         self._mask_right_surf,
        #         -angle
        #     )
        #
        # offset = (surf.size[0] - self.size.x) / 2
        #
        # surf = surf.subsurface(
        #     (offset, offset),
        #     self.size.xy
        # )

        # super()._generate_collision_mask()
        # self.mask = pg.mask.Mask(surf)

    def hit(self, damage: float, hit_by: LogicGameEntity | EllipsisType = ...) -> None:
        if hit_by is not ...:
            if hit_by.is_bullet:
                self._sound.play(pos=self.position)

        if not self.parent:
            super().hit(damage, hit_by)

        self._uses_left -= damage

        if self._uses_left <= 0:
            self.kill(hit_by)

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

            super()._update(delta, keep_position=True)
            return

        else:
            self.size.xy = self._image_size

            # move shield out of way
            self.position.xy = (-1, -1)

        super()._update(delta)

