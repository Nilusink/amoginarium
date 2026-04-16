"""
amoginarium/logic/entities/_collision_relations.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""
from ._collisions import collision_manager, collision_group_bullets, collision_group_islands
from amoginarium.shared.collision_detection import CollisionEvent

def on_collision(obj, event: CollisionEvent) -> None:
    print("HIT", obj, event)


collision_manager.create_relation(collision_group_bullets, collision_group_islands, on_collision, on_collision)

load = None