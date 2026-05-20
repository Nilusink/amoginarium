"""
Central manager for handling all game collision logic.

Registers groups, handles hitboxes,
and establishes bidirectional collision relationships.

Path: amoginarium/logic/entities/_base/_collision/_game_collisions.py
Project: amoginarium
Created: 16.04.2026
Authors: LukasKrah, Nilusink
"""

from __future__ import annotations

import typing as tp

from amoginarium.shared.collision_detection import CollisionManager

if tp.TYPE_CHECKING:
    from amoginarium.shared.collision_detection import CollisionCallbackType
    from amoginarium.shared.collision_detection import CollisionGroupIDType
    from amoginarium.shared.collision_detection import CollisionHitboxType


# noinspection DuplicatedCode
class _GameCollisions:
    """
    Manages the collision groups and relations for the game world.

    Handles the registration of hitboxes and bidirectional collision callbacks.
    """

    __slots__ = (
        "collision_manager",
        "COLLISION_START",
        "COLLISION_END",
        "collision_group_rideable_turrets",
        "collision_group_missiles",
        "collision_group_grenades",
        "collision_group_players",
        "collision_group_bullets",
        "collision_group_islands",
        "collision_group_turrets",
        "collision_group_shields",
        "collision_group_items",
        "all_groups",
        "hitboxes",
        "_registered_relations",
        "__exception_num",
    )

    collision_manager: tp.Final[CollisionManager]
    COLLISION_START: CollisionCallbackType
    COLLISION_END: CollisionCallbackType

    collision_group_rideable_turrets: CollisionGroupIDType
    collision_group_missiles: CollisionGroupIDType
    collision_group_grenades: CollisionGroupIDType
    collision_group_players: CollisionGroupIDType
    collision_group_bullets: CollisionGroupIDType
    collision_group_islands: CollisionGroupIDType
    collision_group_turrets: CollisionGroupIDType
    collision_group_shields: CollisionGroupIDType
    collision_group_items: CollisionGroupIDType

    all_groups: list[CollisionGroupIDType]
    hitboxes: dict[CollisionGroupIDType, CollisionHitboxType]
    _registered_relations: set[tuple[int, int]]
    __exception_num: int

    def __init__(self) -> None:
        self.collision_manager = CollisionManager(
            base_cell_size=500,
            level_dividers=[10],
        )
        self._registered_relations = set()
        self.__exception_num = -1

    def init(
        self, callback_start: CollisionCallbackType, callback_end: CollisionCallbackType
    ) -> None:
        """
        Initialize the collision groups and sets up the default relations.

        :param callback_start: The callback triggered when a collision begins.
        :param callback_end: The callback triggered when a collision ends.
        """
        self.COLLISION_START = callback_start
        self.COLLISION_END = callback_end
        self._setup_groups()

    def _setup_groups(self) -> None:
        """Define collision groups and their relationships."""
        self.collision_group_rideable_turrets = self.collision_manager.add_group(
            max_level=0
        )
        self.collision_group_missiles = self.collision_manager.add_group(
            max_level=1, hitbox_type="obb"
        )
        self.collision_group_grenades = self.collision_manager.add_group(
            max_level=1, hitbox_type="circle"
        )
        self.collision_group_players = self.collision_manager.add_group(max_level=0)
        self.collision_group_bullets = self.collision_manager.add_group(
            max_level=1, hitbox_type="circle"
        )
        self.collision_group_islands = self.collision_manager.add_group(max_level=0)
        self.collision_group_turrets = self.collision_manager.add_group(max_level=0)
        self.collision_group_shields = self.collision_manager.add_group(
            max_level=0, hitbox_type="obb"
        )
        self.collision_group_items = self.collision_manager.add_group(max_level=0)

        self.all_groups = [
            self.collision_group_players,
            self.collision_group_bullets,
            self.collision_group_grenades,
            self.collision_group_islands,
            self.collision_group_turrets,
            self.collision_group_shields,
            self.collision_group_items,
            self.collision_group_missiles,
            self.collision_group_rideable_turrets,
        ]

        self.hitboxes = {  # type: ignore[idk]
            group: self.collision_manager.get_hitbox(group) for group in self.all_groups
        }

        self.create_relations(
            self.collision_group_missiles,
            [
                self.collision_group_rideable_turrets,
                self.collision_group_islands,
                self.collision_group_bullets,
                self.collision_group_turrets,
                self.collision_group_players,
                self.collision_group_grenades,
                self.collision_group_shields,
            ],
        )
        self.create_relations(
            self.collision_group_grenades,
            [
                self.collision_group_missiles,
                self.collision_group_islands,
                self.collision_group_bullets,
                self.collision_group_players,
                self.collision_group_shields,
            ],
        )
        self.create_relations(
            self.collision_group_players,
            [
                self.collision_group_rideable_turrets,
                self.collision_group_missiles,
                self.collision_group_islands,
                self.collision_group_bullets,
                self.collision_group_grenades,
                self.collision_group_items,
                self.collision_group_shields,
            ],
        )
        self.create_relations(
            self.collision_group_bullets,
            [
                self.collision_group_rideable_turrets,
                self.collision_group_missiles,
                self.collision_group_islands,
                self.collision_group_bullets,
                self.collision_group_turrets,
                self.collision_group_players,
                self.collision_group_grenades,
                self.collision_group_shields,
            ],
        )
        self.create_relations(
            self.collision_group_islands,
            [
                self.collision_group_missiles,
                self.collision_group_players,
                self.collision_group_bullets,
                self.collision_group_grenades,
                self.collision_group_shields,
            ],
        )
        self.create_relations(
            self.collision_group_turrets,
            [
                self.collision_group_missiles,
                self.collision_group_bullets,
            ],
        )
        self.create_relations(
            self.collision_group_rideable_turrets,
            [
                self.collision_group_missiles,
                self.collision_group_bullets,
                self.collision_group_players,
            ],
        )
        self.create_relations(
            self.collision_group_shields,
            [
                self.collision_group_missiles,
                self.collision_group_bullets,
                self.collision_group_grenades,
                self.collision_group_islands,
                self.collision_group_players,
            ],
        )

        self.create_relations(
            self.collision_group_items,
            [self.collision_group_players, self.collision_group_islands],
        )

    def create_relations(
        self,
        group_a: CollisionGroupIDType,
        targets: list[CollisionGroupIDType],
    ) -> None:
        """
        Register bidirectional collision relations one group and multiple groups.

        Prevents redundant registration if the relation already exists.

        :param group_a: The ID of the first collision group.
        :param targets: A list of group IDs to collide with.
        """
        for group_b in targets:
            rel_key = (group_a, group_b) if group_a <= group_b else (group_b, group_a)

            if rel_key in self._registered_relations:
                continue

            self.collision_manager.create_relation(
                a_group_id=group_a,
                b_group_id=group_b,
                a_collision_start_callback=self.COLLISION_START,
                b_collision_start_callback=self.COLLISION_START,
                a_collision_end_callback=self.COLLISION_END,
                b_collision_end_callback=self.COLLISION_END,
            )
            self._registered_relations.add(rel_key)

    def add_exception(self) -> int:
        """
        Register a new collision exception rule and returns its unique identifier.

        :return: A unique integer identifier for the collision exception.
        """
        self.__exception_num += 1
        return self.__exception_num


GameCollisions: tp.Final[_GameCollisions] = _GameCollisions()
