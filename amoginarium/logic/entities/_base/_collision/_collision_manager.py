"""
amoginarium/logic/entities/_collisions.py

Project: amoginarium
Created: 16.04.2026
Authors: LukasKrah
"""

import typing as tp

from amoginarium.shared.collision_detection import CollisionManager, CollisionCallback
from ._collision_types import CollisionType, HitboxTypes


class GameCollisions:
    collision_manager: tp.Final[CollisionManager] = CollisionManager(
        base_cell_size=500,
        level_dividers=[10],
    )

    @classmethod
    def init(cls, callback_start: CollisionCallback, callback_end: CollisionCallback) -> None:
        cls.COLLISION_START = callback_start
        cls.COLLISION_END = callback_end

        cls.collision_group_players: tp.Final[CollisionType.GroupID] = cls.collision_manager.add_group(max_level=0)
        cls.collision_group_bullets: tp.Final[CollisionType.GroupID] = cls.collision_manager.add_group(max_level=1,
                                                                                                       hitbox_type="circle")
        cls.collision_group_grenades: tp.Final[CollisionType.GroupID] = cls.collision_manager.add_group(max_level=1,
                                                                                                        hitbox_type="circle")
        cls.collision_group_islands: tp.Final[CollisionType.GroupID] = cls.collision_manager.add_group(max_level=0)
        cls.collision_group_turrets: tp.Final[CollisionType.GroupID] = cls.collision_manager.add_group(max_level=0)
        cls.collision_group_shields: tp.Final[CollisionType.GroupID] = cls.collision_manager.add_group(max_level=0,
                                                                                                       hitbox_type="obb")

        cls.all_groups: tp.Final[list[CollisionType.GroupID]] = [
            cls.collision_group_players,
            cls.collision_group_bullets,
            cls.collision_group_grenades,
            cls.collision_group_islands,
            cls.collision_group_turrets,
            cls.collision_group_shields,
        ]

        cls.hitboxes: tp.Final[dict[CollisionType.GroupID, HitboxTypes]] = {
            collision_group: cls.collision_manager.get_hitbox(collision_group) for collision_group in cls.all_groups
        }

        # Grenades collide with Islands, Bullets, Players
        cls.create_default_relation(cls.collision_group_grenades, cls.collision_group_islands)
        cls.create_default_relation(cls.collision_group_grenades, cls.collision_group_bullets)
        cls.create_default_relation(cls.collision_group_grenades, cls.collision_group_players)

        # Players collide with Islands, Bullets, (Grenades)
        cls.create_default_relation(cls.collision_group_players, cls.collision_group_islands)
        cls.create_default_relation(cls.collision_group_players, cls.collision_group_bullets)

        # Bullets collide with Islands, Bullets, Turrets, (Players, Grenades)
        cls.create_default_relation(cls.collision_group_bullets, cls.collision_group_islands)
        cls.create_default_relation(cls.collision_group_bullets, cls.collision_group_bullets)
        cls.create_default_relation(cls.collision_group_bullets, cls.collision_group_turrets)

        # Shield collides with Bullets, Grenades
        cls.create_default_relation(cls.collision_group_shields, cls.collision_group_bullets)
        cls.create_default_relation(cls.collision_group_shields, cls.collision_group_grenades)

    @classmethod
    def create_default_relation(cls, group_a: CollisionType.GroupID, group_b: CollisionType.GroupID) -> None:
        """
        Registers a bidirectional collision relation between two groups using default callbacks.
        :param group_a: The ID of the first collision group.
        :param group_b: The ID of the second collision group.
        """
        cls.collision_manager.create_relation(
            group_a_id=group_a,
            group_b_id=group_b,
            cb_a_on_start=cls.COLLISION_START,
            cb_b_on_start=cls.COLLISION_START,
            cb_a_on_end=cls.COLLISION_END,
            cb_b_on_end=cls.COLLISION_END
        )

    __slots__ = ()
