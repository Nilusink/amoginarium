"""
amoginarium/logic/entities/_collision_relations.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""
from ._collisions import collision_manager, collision_group_bullets, collision_group_islands

from ._bullets import Bullet


collision_manager.create_relation(collision_group_bullets, collision_group_islands, Bullet.on_collision, None)

load = None