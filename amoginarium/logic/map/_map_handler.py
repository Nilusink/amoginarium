"""
Load and save maps.

Path: amoginarium/logic/map/_map_handler.py
Project: amoginarium
Created: 15.03.2026
Authors: Nilusink
"""

import json

from icecream import ic

from amoginarium.logic.entities import Island
from amoginarium.shared import GameEntityLike

from ..base._groups import Updated
from ._json_serialize import to_str

# from ..entities._


def save_map(filepaht: str) -> None:
    map = {
        "name": "test",
        "background": 2,
        "spawn_pos": [100, 600],
        "platforms": [],
        "entities": [],
    }
    for entity in Updated.entities():
        entity: GameEntityLike
        if isinstance(entity, Island):
            entity: Island

            map["platforms"].append(entity)

        else:
            map["entities"].append(entity)

    with open(filepaht, "w") as file:
        file.write(to_str(map))
