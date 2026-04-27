"""
amoginarium/logic/entities/_collision/collision_hitboxes.py

Project: amoginarium
Created: 27.04.2026
Authors: LukasKrah
"""
from ._collision_manager import CollisionType, HitboxTypes, collision_manager
from .collision_groups import all_groups

# region Hitboxes
hitboxes: dict[CollisionType.GroupID, HitboxTypes] = {
    collision_group: collision_manager.get_hitbox(collision_group) for collision_group in all_groups
}

# endregion
