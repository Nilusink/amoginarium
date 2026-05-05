"""
_missiles.py
05.05.2026

Missile dummies

Author:
Nilusink
"""

from amoginarium.shared import MissileCIDs

from ._bullet import BulletDummy


class MultiStageMissileDummy(BulletDummy):
    _CID = MissileCIDs.multi_stage
