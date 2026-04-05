"""
_player.py
30.03.2026

graphics dummy for player

Author:
Nilusink
"""
import pygame as pg

from amoginarium.base._textures import textures
from amoginarium.shared.utility import Color
from amoginarium.shared import DummyCIDs

from ..entities import Drawn_1
from ._synced_entities import SyncedLRImageEntity
from ..render_bindings import renderer


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
    __slots__ = ["_hp_colors"]

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
        """
        Load the textures for player
        """
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
            parent: int | None = None
    ) -> None:
        super().__init__(sync_id, parent)
        self.add(Drawn_1)

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
        
        # defaults
        self._hp_colors = (
            Color().from_255(255, 0, 0),
            Color().from_255(180, 90, 20),
            Color().from_255(0, 255, 0)
        )

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        if layer == 0:
            super()._gl_draw(delta_cal, layer)

        elif layer == 1:
            # draw health bar
            owp = self.world_position
            renderer.draw_bar(
                (owp.x - self.size.x / 2, owp.y + self.size.y / 2 + 10),
                (self.size.x, 7),
                self._hp_colors,
                self.param0,
            )
