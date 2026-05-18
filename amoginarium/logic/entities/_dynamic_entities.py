"""
Dynamically loaded entities.

Path: amoginarium/logic/entities/_dynamic_entities.py
Project: amoginarium
Created: 20.04.2026
Authors: Nilusink, LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared import DynamicEntityParentViable
from amoginarium.shared.param_entities import load_entities_from_files, ProcessType

from ._weaponry import templates

# gets all base-entities (BaseTurret, BaseWeapon, ...) from templates module
_base_entities: dict[str, tp.Type[DynamicEntityParentViable]] = {
    e.cid(): e
    for e in [
        attr
        for a in dir(templates)  # lists attributes of module
        if not a.startswith("_")  # checks if module is private / protected
        for attr in [getattr(templates, a)]  # converts string name to actual attribute
        if hasattr(attr, "has_cid") and attr.has_cid()  # checks if it is a base entity
    ]
}


new = load_entities_from_files(ProcessType.logic, _base_entities)
new.update(_base_entities)
DYNAMIC_ENTITIES = new
