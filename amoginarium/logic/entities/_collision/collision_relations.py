"""
amoginarium/logic/entities/_collision_relations.py

Project: amoginarium
Created: 17.04.2026
Authors: LukasKrah
"""

from .._base_entities import PositionedLogicEntity
from .collision_manager import collision_manager

collision_group_players = collision_manager.add_group(max_level=0)
collision_group_bullets = collision_manager.add_group(max_level=1)
collision_group_islands = collision_manager.add_group(max_level=0)
collision_group_turrets = collision_manager.add_group(max_level=0)

callback = PositionedLogicEntity.on_collision

collision_manager.create_relation(
    group_a_id=collision_group_bullets,
    group_b_id=collision_group_islands,
    cb_a=callback,
    cb_b=callback
)
