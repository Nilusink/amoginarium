"""
_turrets.py
01.04.2026

turret dummies

Author:
Nilusink
"""

import ctypes
import typing as tp
from types import EllipsisType

from icecream import ic  # noqa: F401

from amoginarium import pv
from amoginarium.shared import TurretCIDs
from amoginarium.shared.utility import Color, MASK16, MASK32, MASK64
from amoginarium.shared.utility import normalize_angle, Vec2

from ..entities import Drawn_1, Drawn_2
from ..render_bindings import renderer
from ..textures import textures
from ._synced_entities import SE_MANAGER, SyncedGraphicsEntity


class BaseTurretDummy(SyncedGraphicsEntity):
    """
    ``param0`` health
    ``param3`` target pos (x=0-31, y=32-63)
    ``param4`` engagement range & valid_angles (min=0-15, max=16-31),
        (start=32-47, end=48-63)
    """

    __slots__ = ["_target_pos", "_range", "_angles", "_hp_colors"]
    _CID = TurretCIDs.base
    _body_texture: int = ...
    _image_name = "mortar_turret_base"
    _image_mirror: str = ""
    _default_size = (23, 24)
    _default_layer: int = 0

    def __new__(cls, *args, **kwargs):
        # only load texture once
        if cls._body_texture is ...:
            cls.load_textures()

        return super().__new__(cls)

    @classmethod
    def load_textures(cls) -> None:
        cls._body_texture, _ = textures.get_texture(
            cls._image_name, cls._default_size, cls._image_mirror, pixel_perfect=True
        )

    def __init__(self, sync_id: int, weapon_id: int) -> None:
        self._target_pos: Vec2 | None = None
        self._range = (0, 0)
        self._angles = (-1, -1)
        super().__init__(sync_id=sync_id)
        self.add(Drawn_1, Drawn_2)

        # defaults
        self.add_child(SE_MANAGER.get_entity(weapon_id))
        self._hp_colors = (
            Color().from_255(255, 0, 0),
            Color().from_255(180, 90, 20),
            Color().from_255(0, 255, 0),
        )

    def _before_gl_draw(self, drawn: bool, layer: int = 0) -> None:
        """
        update targeting pos before drawing
        """
        super()._before_gl_draw(drawn)

        if self.param3 < MASK64:
            x = ctypes.c_int32(self.param3 & MASK32).value
            y = ctypes.c_int32((self.param3 >> 32) & MASK32).value
            self._target_pos = Vec2().from_cartesian(x, y)

        else:
            self._target_pos = None

        self._range = (self.param4 & MASK16, self.param4 >> 16 & MASK16)

        start_angle = self.param4 >> 32 & MASK16
        end_angle = self.param4 >> 48 & MASK16

        self._angles = (
            start_angle / 10_000 if start_angle < MASK16 else -1,
            end_angle / 10_000 if end_angle < MASK16 else -1,
        )

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        # only draw engagement range if on screen
        world_position = pv.global_vars.get_world_position()
        resolution = pv.global_vars.resolution_screen
        if (
            self.pos.x + self._range[1] < world_position.x
            or self.pos.x - self._range[1] > world_position.x + resolution.x
            or self.pos.y + self._range[1] < world_position.y
            or self.pos.y - self._range[1] > world_position.y + resolution.y
        ):
            return

        engage_center = self.world_position

        # draw engagement range
        if layer == 1:
            if self._angles[0] > 0:
                min_1_angle = self._angles[0]
                min_2_angle = self._angles[1]

                min_1 = Vec2().from_polar(min_1_angle, self._range[0])
                min_2 = Vec2().from_polar(min_2_angle, self._range[0])

                max_1 = Vec2().from_polar(min_1_angle, self._range[1])
                max_2 = Vec2().from_polar(min_2_angle, self._range[1])

                renderer.draw_line(
                    engage_center + min_1,
                    engage_center + max_1,
                    Color().from_1(1, 1, 1),
                )

                renderer.draw_line(
                    engage_center + min_2,
                    engage_center + max_2,
                    Color().from_1(1, 1, 1),
                )

                angle_delta = abs(normalize_angle(self._angles[1] - self._angles[0]))
                segments = int(64 * (angle_delta / (2 * 3.1415926)))

                renderer.draw_partial_dashed_circle(
                    engage_center,
                    self._range[1],
                    max_1,
                    max_2,
                    num_segments=segments,
                    color=Color().from_1(1, 1, 1),
                    thickness=3,
                )

                if self._range[0] > 0:
                    renderer.draw_partial_dashed_circle(
                        engage_center,
                        self._range[0],
                        max_1,
                        max_2,
                        num_segments=segments // 2,
                        color=(1, 0.5, 0),
                        thickness=2,
                    )

            else:
                renderer.draw_dashed_circle(
                    engage_center,
                    self._range[1],
                    2048,
                    Color().from_1(1, 1, 1),
                    draw_len=32,
                    gap_len=32,
                    thickness=3,
                )

                if self._range[0] > 0:
                    renderer.draw_dashed_circle(
                        engage_center,
                        self._range[0],
                        2048,
                        (1, 0.5, 0),
                        draw_len=32,
                        gap_len=32,
                        thickness=3,
                    )

            # draw sensor ranges
            super()._gl_draw(delta_cal)

            # targets
            if pv.global_vars.show_targets:
                if self._target_pos:
                    renderer.draw_line(
                        self.world_position,
                        self._target_pos - world_position,
                        Color().from_255(255, 0, 0, 100),
                    )
                    renderer.draw_circle(
                        self._target_pos - world_position,
                        64,
                        32,
                        Color().from_255(255, 0, 0, 100),
                    )

                renderer.draw_line(
                    self.world_position,
                    self.world_position
                    + Vec2().from_polar(self.facing.angle, self._range[1]),
                    Color().from_255(150, 200, 0),
                )

        # only draw turret if on screen
        if (
            self.pos.x + self.size.x / 2 < world_position.x
            or self.pos.x - self.size.x / 2 > world_position.x + resolution.x
            or self.pos.y + self.size.y / 2 < world_position.y
            or self.pos.y - self.size.y / 2 > world_position.y + resolution.y
        ):
            return

        if layer == 1:
            if self.facing.x < 0:
                renderer.draw_textured_quad(
                    self._body_texture,
                    self.world_position - self.size / 2,
                    self.size,
                    layer=self._default_layer,
                    # force_draw=self._highlight
                )

            else:
                # mirror turret
                renderer.draw_textured_quad(
                    self._body_texture,
                    self.world_position
                    - Vec2().from_cartesian(-self.size.x / 2, self.size.y / 2),
                    (-self.size.x, self.size.y),
                    layer=self._default_layer,
                    # force_draw=self._highlight,
                )

        elif layer == 2:
            # draw health bar
            owp = self.world_position
            renderer.draw_bar(
                (owp.x - self.size.x / 2, owp.y + self.size.y / 2 + 10),
                (self.size.x, 7),
                self._hp_colors,
                self.param0,
            )


class ExactoSniperTurretDummy(BaseTurretDummy):
    __slots__ = []
    _CID = TurretCIDs.exacto_sniper


class RideableTurret(BaseTurretDummy):
    _CID = TurretCIDs.rideable_base


class CalculatedRideableTurretDummy(BaseTurretDummy):
    _CID = TurretCIDs.rideable_calculated

    _reticle_texture: tp.ClassVar[int | EllipsisType] = ...
    __size = Vec2().from_cartesian(31, 31) * 2

    @classmethod
    def load_textures(cls) -> None:
        cls._reticle_texture, _ = textures.get_texture(
            "reticle", (31, 31), pixel_perfect=True
        )
        super().load_textures()

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        super()._gl_draw(delta_cal, layer)

        if layer == 1 and self._get_bit("flags", 14):
            if self._target_pos.length != 0:
                pos = (
                    pv.global_vars.translate_screen_coord(
                        self._target_pos - pv.global_vars.get_world_position(),
                    )
                    - self.__size / 2
                )
                renderer.draw_textured_quad(
                    self._reticle_texture,
                    pos,
                    self.__size,
                    layer=1,
                    offscreen_check=True,
                    convert_global=False,
                )
