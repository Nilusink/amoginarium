"""
Vehicle graphics representations.

| ``Path``: amoginarium/graphics/logic_dummies/_vehicles.py
| ``Project``: amoginarium
| ``Created``: 21.05.2026
| ``Authors``: Nilusink
"""

from amoginarium.shared import VehicleCIDs

from ._turrets import RideableTurret


class BaseVehicleDummy(RideableTurret):
    _CID = VehicleCIDs.base
