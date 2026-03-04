"""
amoginarium/base/_maps.py

Project: amoginarium
"""
import json
import os
import typing as tp

from icecream import ic

from amoginarium.logic import Vec2
import pygame as pg


##################################################
#                     Code                       #
##################################################

class Maps:
    """
    temp solution until extended
    """

    def load_map(self, map_path: tp.LiteralString) -> None:
        """
        load a map from a json file
        """
        if not os.path.isfile(map_path):
            # if the file wasn't found, try adding the root program path
            map_path = os.path.dirname(__file__) + "/" + map_path
            ic(map_path)
            if not os.path.isfile(map_path):
                raise FileNotFoundError(f"Couldn't find map \"{map_path}\"")

        # load map data
        data = json.load(open(map_path, "r"))
        self._last_loaded = map_path

        pg.display.set_caption(f"amoginarium - {data["name"]}")
        Players.spawn_point = Vec2.from_cartesian(*data["spawn_pos"])

        # set background
        if 0 <= data["background"] - 1 <= len(self._backgrounds):
            self._background = self._backgrounds[data["background"] - 1]

        else:
            self._background = self._backgrounds[0]

        # check if background has been assigned
        if not self._background.loaded:
            self._background.load_textures()

        # # spwan a lot of bulllets
        # Players.spawn_point = Vec2.from_cartesian(950, -100)
        # n_bullets = 150
        # x_spacing = global_vars.screen_size.x / n_bullets

        # for i in range(n_bullets):
        #     Bullet(
        #          self,
        #          Vec2.from_cartesian(0 + x_spacing*i, 0),
        #          Vec2.from_cartesian(0, 100), time_to_life=5
        #     )
        #     Bullet(
        #          self,
        #          Vec2.from_cartesian(0 + x_spacing*i, 100),
        #          Vec2.from_cartesian(0, 100), time_to_life=5
        #     )
        # return

        # load islands
        for island in data["platforms"]:
            if "size" in island:
                Island(
                    Vec2.from_cartesian(*island["pos"]),
                    size=Vec2.from_cartesian(*island["size"]),
                )

            elif "form" in island:
                Island(
                    Vec2.from_cartesian(*island["pos"]),
                    form=island["form"],
                )

            else:
                print_ic_style(
                    f"{CC.fg.RED}invalid island: "
                    f"{CC.fg.YELLOW}{island}"
                )

        # load entities
        for entity in data["entities"]:
            if entity["type"] not in SPAWNABLES:
                print_ic_style(
                    f"{CC.fg.RED}unknown entity: "
                    f"{CC.fg.YELLOW}{entity["type"]}"
                )
                continue

            # check if arguments were given
            args = {}
            if "args" in entity:
                args = entity["args"]

            try:
                SPAWNABLES[entity["type"]](
                    Coalitions.red,
                    Vec2.from_cartesian(*entity["pos"]),
                    **args
                )

            except TypeError:
                print_ic_style(
                    f"{CC.fg.RED}invalid arguments for "
                    f"{CC.fg.YELLOW}{entity["type"]}{CC.fg.RED}: "
                    f"\"{CC.fg.YELLOW}{args}{CC.fg.RED}\""
                )
