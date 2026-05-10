"""
_player.py
30.03.2026

graphics dummy for player

Author:
Nilusink
"""
from icecream import ic
import pygame as pg

from amoginarium.base._textures import textures
from amoginarium.shared.utility import Color
from amoginarium.shared import DummyCIDs
from amoginarium import pv

from ..entities import Drawn_1, Drawn_2
from ..render_bindings import renderer
from ._synced_entities import SyncedLRImageEntity, SE_MANAGER
from ._inventory import Inventory


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
    __slots__ = ["_hp_colors", "_hotbar", "_inventory"]

    _CID = DummyCIDs.player

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
            i_id: int,
            h_id: int,
            size: int = 64,
            parent: int | None = None
    ) -> None:
        super().__init__(sync_id, parent)
        self._draw_children = False
        self.add(Drawn_1, Drawn_2)

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

        # inventories
        self._hotbar: Inventory = Inventory(h_id, self)
        self._inventory: Inventory = Inventory(i_id, self)

    def _gl_draw(self, delta_cal: float, layer: int = 0):
        if layer == 0:
            super()._gl_draw(delta_cal, layer)

        elif layer == 1:
            # check if item
            if self._hotbar.buff.selected < self._hotbar.buff.size:
                item = self._hotbar.buff.slots[self._hotbar.buff.selected]
                entity = SE_MANAGER.get_entity(item.item_id)

                if entity:
                    if item.count > 0 and item.item_id > 0:
                        self.add_child(entity)

                    else:
                        self.remove_child(entity)

            # draw health bar
            owp = self.world_position
            renderer.draw_bar(
                (owp.x - self.size.x / 2, owp.y + self.size.y / 2 + 10),
                (self.size.x, 7),
                self._hp_colors,
                self.param0,
            )

        elif layer == 2:
            # draw inventory
            if self._get_bit("flags", 15):  # in inventory
                screen_size = pv.global_vars.get_screen_size()
                # background
                renderer.draw_rounded_rect(
                    (screen_size.x * 0.25, screen_size.y * 0.1),
                    (screen_size.x * 0.5, screen_size.y * 0.8),
                    Color().from_255(80, 80, 80),
                    20,
                    convert_global=False,
                )

                # slots
                self._inventory.draw_at(
                    (0.5, 0.65),
                    10,
                    0.5,
                    delta_cal,
                    layer=layer
                )
                self._hotbar.draw_at(
                    (0.5, 0.85),
                    10,
                    0.5,
                    delta_cal,
                    layer=layer
                )

                # character display
                renderer.draw_rounded_rect(
                    (screen_size.x * 0.28, screen_size.y * 0.17),
                    (self.size.x * 3, self.size.y * 4),
                    Color().from_255(50, 50, 50),
                    20,
                    convert_global=False
                )
            
            else:
                self._hotbar.draw_at(
                    (0.5, 0.95),
                    10,
                    0.4,
                    delta_cal,
                    layer=layer
                )
