"""
Exports core collision management and event handling interfaces.

| ``Path``: amoginarium/shared/collision_detection/__init__.py
| ``Project``: amoginarium
| ``Created``: 13.04.2026
| ``Authors``: LukasKrah
"""

from ._collision_event import CollisionEvent
from ._collision_manager import CollisionManager
from ._collision_types import CollisionCallbackType, CollisionEntityIDType
from ._collision_types import CollisionEventIDType, CollisionExceptionIDType
from ._collision_types import CollisionGroupIDType, CollisionHitboxType
from ._collision_types import CollisionRelationIDType, CollisionTypes
