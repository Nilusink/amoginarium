"""
_dynamic_entities.py
20.04.2026

dynamically loaded entities

Author:
Nilusink
"""
"""
_spawnables.py
15.03.2026

collects every spawn-able entity

Author:
Nilusink
"""

import typing as tp

from amoginarium.shared.param_entities import load_entities_from_files, ProcessType

from ._base_entity import LogicGameEntity
from ._static_turrets import BaseTurret
from ._weapons import FileLoadedWeapon
from ._bullets import Bullet
from ._sensors import MagicSensor
from ._radar import RadarSensor


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
