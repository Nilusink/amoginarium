"""
_load_from_files.py
20.04.2026

load entities from files

Author:
Nilusink
"""

from pathlib import Path
from icecream import ic
from enum import Enum
import typing as tp
import tomllib

from amoginarium.shared.utility import Vec2
from amoginarium.shared.audio import SoundEffect, RandomizedEffect, PRESETS
from amoginarium.shared.audio import ScopedRandomizedEffect, PresetEffect
from amoginarium.shared.audio import ContinuousSoundEffect


BASE_DIR = "./assets/entities/"
_GRAPHICS_KEYS = ("image", "trace")


class ProcessType(Enum):
    base = 0
    logic = 1


class _ResolveThis:
    """entities specified as CIDs"""

    def __init__(self, entity_cid: str) -> None:
        self._cid = entity_cid

    def resolve(self, entity_index: dict[str, tp.Type]) -> tp.Type:
        """resolve string"""
        return entity_index[self._cid]


def check_value[A](value: A, convert_vec2: bool = False) -> A | _ResolveThis:
    """checks if a value needs to be resolved"""

    if isinstance(value, str):
        if value.startswith("<") and value.endswith(">"):
            return _ResolveThis(value.lstrip("<").rstrip(">"))

    if convert_vec2 and isinstance(value, list):
        # only convert values with length of 2
        if len(value) != 2:
            return value

        # make sure values are numbers
        for val in value:
            if not isinstance(val, (float, int)):
                return value

        return Vec2().from_cartesian(value[0], value[1])

    return value


def _cid(cls):
    """return cid encased in an object.value (to mimic enum)"""
    # noinspection PyTypeChecker
    return cls._cid


def load_entities_from_files(
        process_type: ProcessType,
        entity_index: dict[str, tp.Type],
        directory: str = BASE_DIR
) -> dict[str, tp.Type]:
    """load all entities specified in assets"""

    entity_index = entity_index.copy()
    new_entities: dict[str, tp.Type] = {}

    # inherits form other dynamic entities 
    to_inherit = {}

    for file in Path(directory).rglob("*.toml", case_sensitive=False):
        with open(file, "rb") as f:
            lazy_inherit = False
            # ignore examples folder
            if file.parent.parts[-1] == "examples":
                continue

            # load file
            data = tomllib.load(f)

            # make sure required data exists
            if "id" not in data:
                ic(file, "failed")
                continue

            if "cid" not in data["id"]:
                ic(file, "failed")
                continue

            cid: str = data["id"]["cid"]

            if "from" not in data["id"]:
                ic(file, "failed")
                continue

            # try to find parent entity
            if data["id"]["from"] not in entity_index:
                lazy_inherit = True

            class_name = f"File{"".join([p.capitalize() for p in data["id"]["cid"].split(".")])}"

            __dict: dict[str, tp.Any] = {
                "_cid": cid,
                "cid": classmethod(_cid)
            }
            # fill dict
            if "visibility" in data:
                if "size" in data["visibility"]:
                    size: Vec2 | float | list[float] = data["visibility"]["size"]

                    # convert size if not Vec2
                    if isinstance(size, float):
                        size: Vec2 = Vec2().from_cartesian(size, size)

                    elif isinstance(size, list):
                        size: Vec2 = Vec2().from_cartesian(size[0], size[1])

                    __dict["_default_size"] = size

                if process_type == ProcessType.base:
                    for key, value in data["visibility"].items():
                        if key == "size":
                            continue

                        __dict[f"_default_{key}"] = check_value(value)

            # behaviour
            if process_type == ProcessType.logic:
                if "behaviour" in data:
                    for key, value in data["behaviour"].items():
                        __dict[f"_default_{key}"] = check_value(value)

                if "sound" in data:
                    effect: (
                        tp.Type[SoundEffect | RandomizedEffect | ContinuousSoundEffect]
                        | None
                    ) = None
                    if "name" in data["sound"]:
                        sound_name: str | list[str] = data["sound"]["name"]

                        if isinstance(sound_name, list):
                            sound_class_name = "".join(
                                [p.capitalize() for p in sound_name]
                            )
                        
                        else:
                            sound_class_name = sound_name.capitalize()

                        # noinspection PyTypeChecker
                        effect: tp.Type[PresetEffect] = type(
                            f"{sound_class_name}Effect",
                            (PresetEffect,),
                            {"_sound_name": sound_name}
                        )
                    
                    if "scope" in data["sound"]:
                        sound_scope: str = data["sound"]["scope"]

                        # noinspection PyTypeChecker
                        effect: tp.Type[ScopedRandomizedEffect] = type(
                            f"{sound_scope.capitalize()}Effect",
                            (ScopedRandomizedEffect,),
                            {"_scope": sound_scope}
                        )
                    
                    if "preset" in data["sound"]:
                        preset = data["sound"]["preset"]
                        if preset in PRESETS:
                            effect = PRESETS[preset]
                    
                    if effect:
                        __dict["_default_sound_effect"] = effect

            for subsection in data:
                if process_type == ProcessType.logic:
                    if (
                        subsection
                        in ("id", "visibility", "behaviour", "image", "sound")
                        + _GRAPHICS_KEYS
                    ):
                        continue

                    elif subsection.startswith("sensor"):
                        __dict["_sensors_list"] = list(data[subsection].values())
                        continue

                elif process_type == ProcessType.base:
                    if subsection not in _GRAPHICS_KEYS:
                        continue

                for key, value in data[subsection].items():
                    if process_type == ProcessType.logic:
                        dict_key = f"_default_{subsection}_{key}"
                        value = check_value(value, False)

                    else:
                        dict_key = f"_{subsection}_{key}"
                        value = check_value(value, True)

                    __dict[dict_key] = value

            if not lazy_inherit:
                parent_class = entity_index[data["id"]["from"]]

                # noinspection PyTypeChecker
                new_class: tp.Type = type(
                    class_name,
                    (parent_class,),
                    __dict
                )  # type: ignore[assignment]
                new_entities[cid] = new_class

            else:
                to_inherit[cid] = (class_name, data["id"]["from"], __dict)

    for _ in range(len(to_inherit)):
        for cid, params in to_inherit.copy().items():
            if params[1] not in new_entities and params[1] not in to_inherit:
                ic(cid, "failed: inherit", params[1])
                to_inherit.pop(cid)
                continue

            # if inheritance is possible, append to entity index
            if params[1] in new_entities:
                new_entities[cid] = type(
                    params[0],
                    (new_entities[params[1]],),
                    params[2]
                )
                to_inherit.pop(cid)

        if not to_inherit:
            break

    else:
        raise RuntimeError(f"Circular dependancy detected: {list(to_inherit.keys())}")

    entity_index.update(new_entities)

    names = [c.__name__ for c in entity_index.values()]

    # resolve stuff
    for entity in new_entities.values():
        for key, item in entity.__dict__.items():
            if isinstance(item, _ResolveThis):
                try:
                    setattr(entity, key, item.resolve(entity_index))

                except KeyError:
                    ic(entity, key)

            elif key == "_sensors_list":
                preset_sensors = item
                sensors = []
                for sensor in preset_sensors:
                    try:
                        sensor["type"] = entity_index[
                            sensor["type"].lstrip("<").rstrip(">")
                        ]
                        sensors.append(sensor)

                    except KeyError:
                        ic(entity, sensor)

                setattr(entity, key, sensors)

    return new_entities
