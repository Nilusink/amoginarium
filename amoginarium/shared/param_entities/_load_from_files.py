"""
Load entities from files.

| ``Path``: amoginarium/shared/param_entities/_load_from_files.py
| ``Project``: amoginarium
| ``Created``: 20.04.2026
| ``Authors``: Nilusink
"""

import tomllib
import typing as tp
from enum import Enum
from pathlib import Path

from icecream import ic

from amoginarium.shared.audio import PresetEffect, PRESETS, ScopedRandomizedEffect
from amoginarium.shared.utility import Vec2

if tp.TYPE_CHECKING:
    from amoginarium.shared.audio import ContinuousSoundEffect
    from amoginarium.shared.audio import RandomizedEffect, SoundEffect

BASE_DIR = "./assets/entities/"
_GRAPHICS_KEYS = ("image", "trace")
_SHARED_KEYS = ("bullet",)


class ProcessType(Enum):
    """defines logic or base / render process."""

    base = 0
    logic = 1


class _ResolveThis:
    """entities specified as CIDs."""

    def __init__(self, entity_cid: str) -> None:
        self._CID = entity_cid

    def resolve(self, entity_index: dict[str, type]) -> type:
        """Resolve string."""
        return entity_index[self._CID]


def check_value[A](value: A, convert_vec2: bool = False) -> A | _ResolveThis:
    """Checks if a value needs to be resolved."""
    if isinstance(value, str) and value.startswith("<") and value.endswith(">"):
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
    """Return cid encased in an object.value (to mimic enum)."""
    # noinspection PyTypeChecker
    return cls._CID


def load_entities_from_files(
    process_type: ProcessType,
    entity_index: dict[str, type],
    directory: str = BASE_DIR,
) -> dict[str, type]:
    """Load all entities specified in assets."""
    entity_index = entity_index.copy()
    new_entities: dict[str, type] = {}

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

            class_name = f"File{
                ''.join(
                    [
                        p.capitalize()
                        for s in data['id']['cid'].split('.')
                        for p in s.split('_')
                    ]
                )
            }"

            dict_: dict[str, tp.Any] = {"_CID": cid, "cid": classmethod(_cid)}
            # fill dict
            if "visibility" in data:
                if "size" in data["visibility"]:
                    size: Vec2 | float | list[float] = data["visibility"]["size"]

                    # convert size if not Vec2
                    if isinstance(size, float):
                        size: Vec2 = Vec2().from_cartesian(size, size)

                    elif isinstance(size, list):
                        size: Vec2 = Vec2().from_cartesian(size[0], size[1])

                    dict_["_default_size"] = size

                if process_type == ProcessType.base:
                    for key, value in data["visibility"].items():
                        if key == "size":
                            continue

                        dict_[f"_default_{key}"] = check_value(value)

            # behaviour
            if process_type == ProcessType.logic:
                if "behaviour" in data:
                    for key, value in data["behaviour"].items():
                        dict_[f"_default_{key}"] = check_value(value)

                if "sound" in data:
                    effect: (
                        type[SoundEffect | RandomizedEffect | ContinuousSoundEffect]
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
                        effect: type[PresetEffect] = type(
                            f"{sound_class_name}Effect",
                            (PresetEffect,),
                            {"_sound_name": sound_name},
                        )

                    if "scope" in data["sound"]:
                        sound_scope: str = data["sound"]["scope"]

                        # noinspection PyTypeChecker
                        effect: type[ScopedRandomizedEffect] = type(
                            f"{sound_scope.capitalize()}Effect",
                            (ScopedRandomizedEffect,),
                            {"_scope": sound_scope},
                        )

                    if "preset" in data["sound"]:
                        preset = data["sound"]["preset"]
                        if preset in PRESETS:
                            effect = PRESETS[preset]

                    if effect:
                        if "volume" in data["sound"]:
                            effect.volume = data["sound"]["volume"]

                        dict_["_default_sound_effect"] = effect

            for subsection in data:
                if process_type == ProcessType.logic:
                    if (
                        subsection
                        in ("id", "visibility", "behaviour", "image", "sound")
                        + _GRAPHICS_KEYS
                    ):
                        continue

                    if subsection.startswith("sensor"):
                        dict_["_sensors_list"] = list(data[subsection].values())
                        continue

                    # check if list
                    k0: str = next(iter(data[subsection].keys()))

                    if k0.isnumeric() and isinstance(data[subsection][k0], dict):
                        # if is list, append to values and continue
                        dict_[f"_default_{subsection}"] = list(
                            data[subsection].values()
                        )
                        continue

                elif process_type == ProcessType.base:
                    if subsection not in (_GRAPHICS_KEYS + _SHARED_KEYS):
                        continue

                for key, value in data[subsection].items():
                    if process_type == ProcessType.logic:
                        dict_key = f"_default_{subsection}_{key}"
                        value = check_value(value, False)

                    else:
                        dict_key = f"_{subsection}_{key}"
                        value = check_value(value, True)

                    dict_[dict_key] = value

            if not lazy_inherit:
                parent_class = entity_index[data["id"]["from"]]

                # noinspection PyTypeChecker
                new_class: type = type(class_name, (parent_class,), dict_)  # type: ignore[assignment]
                new_entities[cid] = new_class

            else:
                to_inherit[cid] = (class_name, data["id"]["from"], dict_)

    for _ in range(len(to_inherit)):
        for cid, params in to_inherit.copy().items():
            if params[1] not in new_entities and params[1] not in to_inherit:
                ic(process_type, cid, "failed: inherit", params[1])
                to_inherit.pop(cid)
                continue

            # if inheritance is possible, append to entity index
            if params[1] in new_entities:
                new_entities[cid] = type(
                    params[0], (new_entities[params[1]],), params[2]
                )
                to_inherit.pop(cid)

        if not to_inherit:
            break

    else:
        msg = f"Circular dependency detected: {list(to_inherit.keys())}"
        raise RuntimeError(msg)

    entity_index.update(new_entities)

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
                        ic(entity, sensor, entity_index)

                setattr(entity, key, sensors)

    return new_entities
