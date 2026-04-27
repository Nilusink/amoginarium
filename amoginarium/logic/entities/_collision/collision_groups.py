"""
amoginarium/logic/entities/_collision_relations.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

from ._collision_manager import collision_manager, CollisionType

collision_group_players: CollisionType.GroupID = collision_manager.add_group(max_level=0)
collision_group_bullets: CollisionType.GroupID = collision_manager.add_group(max_level=1, hitbox_type="circle")
collision_group_grenades: CollisionType.GroupID = collision_manager.add_group(max_level=1, hitbox_type="circle")
collision_group_islands: CollisionType.GroupID = collision_manager.add_group(max_level=0)
collision_group_turrets: CollisionType.GroupID = collision_manager.add_group(max_level=0)
collision_group_shields: CollisionType.GroupID = collision_manager.add_group(max_level=0, hitbox_type="obb")

all_groups: list[CollisionType.GroupID] = [
    collision_group_players,
    collision_group_bullets,
    collision_group_grenades,
    collision_group_islands,
    collision_group_turrets,
    collision_group_shields,
]
