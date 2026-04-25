"""
_dynamic_entities.py
20.04.2026

dynamically loaded entities

Author:
Nilusink
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared.param_entities import load_entities_from_files, ProcessType

from ._base_entities import LogicGameEntity
from ._turrets import BaseTurret
from ._weapons import FileLoadedWeapon
from ._bullets import Bullet
from ._sensors import MagicSensor
from ._sensors import RadarSensor


# noinspection PyTypeChecker
_base_entities: dict[str, tp.Type[LogicGameEntity]] = {
    e.cid(): e for e in [
        BaseTurret,
        FileLoadedWeapon,
        Bullet,
        MagicSensor,
        RadarSensor
    ]
}

new = load_entities_from_files(ProcessType.logic, _base_entities)
new.update(_base_entities)
DYNAMIC_ENTITIES = new
