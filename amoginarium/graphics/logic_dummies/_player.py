"""
_player.py
30.03.2026

graphics dummy for player

Author:
Nilusink
"""
from icecream import ic
import pygame as pg
import typing as tp

from ._synced_entities import SyncedLRImageEntity
from ..entities import Drawn
from ...base._textures import textures
from ...shared import DummyCIDs
from ...shared.utility import Vec2

PLAYER_LEFT_64_PATH = "amogus64left"
PLAYER_RIGHT_64_PATH = "amogus64right"
PLAYER_OOB_RIGHT_64_PATH = "amogusOOB64right"
PLAYER_OOB_LEFT_64_PATH = "amogusOOB64left"

PIXEL_MASK = pg.mask.Mask((1, 1), True)
PIXEL_LINE_VERTICAL = pg.mask.Mask((1, 32), True)


class PlayerDummy(SyncedLRImageEntity):
    """
    `param0` health (0-1)
    """
    __slots__ = []

    _cid = DummyCIDs.player

    _player_right_64_texture: int = ...
    _player_left_64_texture: int = ...
    _player_oob_right_1_texture: int = ...
    _player_oob_right_2_texture: int = ...
    _player_oob_left_1_texture: int = ...
    _player_oob_left_2_texture: int = ...

    def __new__(cls, *args, **kwargs):
        # only load texture once
        if cls._player_left_64_texture is ...:
            cls.load_textures()

        return super(PlayerDummy, cls).__new__(cls)

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
            sync_id: int,
            size: int = 64,
            parent: tp.Self | None = None
    ) -> None:
        super().__init__(sync_id, parent)

        # load textures
        if size == 64:
            self._texture_id_r = self._player_right_64_texture
            self._texture_id_l = self._player_left_64_texture

        else:
            self._texture_id_r, _ = textures.get_texture(
                PLAYER_RIGHT_64_PATH,
                (size, size)
            )
            self._texture_id_l, _ = textures.get_texture(
                PLAYER_RIGHT_64_PATH,
                (size, size),
                mirror="x"
            )

    def _gl_draw(
            self,
            delta_cal: float,
            draw_at: Vec2 = ...,
            size: Vec2 = ...,
            convert_global: bool = True
    ):
        super()._gl_draw(delta_cal, draw_at, size, convert_global)
