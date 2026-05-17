"""
_json_serialize.py
15.03.2026

convert everything ingame to a str

Author:
Nilusink
"""

import json
import re

from amoginarium.logic.entities import LogicGameEntity
from amoginarium.shared.utility import Vec2


class Inline:
    def __init__(self, data):
        self.data = data


def preprocess(obj):
    if isinstance(obj, list):
        if obj and all(isinstance(x, (int, float)) for x in obj):
            return Inline(obj)

        return [preprocess(x) for x in obj]

    if isinstance(obj, dict):
        return {k: preprocess(v) for k, v in obj.items()}

    return obj


def float_to_str(value: float | int) -> str:
    if value.is_integer():
        return str(int(value))

    return str(value)


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Inline):
            return f"@@{', '.join(map(float_to_str, obj.data))}@@"

        elif isinstance(obj, Vec2):
            return f"@@{', '.join(map(float_to_str, obj.xy))}@@"

        elif isinstance(obj, LogicGameEntity):
            return preprocess(obj.to_dict())

        return super().default(obj)


def to_str(game_state: dict | list) -> str:
    out = json.dumps(
        preprocess(game_state),
        indent=4,
        cls=Encoder,
    )
    return re.sub(r'"@@(.*?)@@"', r'[\1]', out)
