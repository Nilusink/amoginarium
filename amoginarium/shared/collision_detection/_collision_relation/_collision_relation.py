"""
amoginarium/shared/collision_detection/_collision_relation.py

Project: amoginarium
Created: 14.04.2026
Authors: LukasKrah
"""

import typing as tp
from types import EllipsisType

from .._collision_group import (
    CollisionGroup,
    CollisionHitBox,
    CollisionGroupEntityData
)
from .._collision_methods import CollisionMethod, CollisionMethods
from .._collision_event import CollisionCallback


class CollisionRelation[T1, T2]:
    __slots__ = (
        "__group_a", "__group_b", "__collision_method",
        "__callback_a", "__callback_b",
        "__list_a", "__list_b", "__grid_b", "__collision_func",
        "__a_px_o", "__a_py_o", "__a_px_n", "__a_py_n", "__a_sx", "__a_sy",
        "__b_px_o", "__b_py_o", "__b_px_n", "__b_py_n", "__b_sx", "__b_sy"
    )

    def __init__(
            self,
            *,
            group_a: CollisionGroup[T1],
            group_b: CollisionGroup[T2],
            on_collision_a: CollisionCallback[T1, T2] | None = None,
            on_collision_b: CollisionCallback[T2, T1] | None = None,
            collision_method: CollisionMethod | EllipsisType = ...,
    ) -> None:
        self.__group_a = group_a
        self.__group_b = group_b
        self.__callback_a = on_collision_a
        self.__callback_b = on_collision_b

        if collision_method == ...:
            if self.__group_a.hitbox_type == CollisionHitBox.aabb and self.__group_b.hitbox_type == CollisionHitBox.aabb:
                collision_method = CollisionMethods.aabb_aabb.Cython

        self.__collision_method = collision_method

        self.__list_a = self.__group_a.entities
        self.__list_b = self.__group_b.entities
        self.__grid_b = getattr(self.__group_b, "grid", {})
        self.__collision_func = self.__collision_method.collision

        # Cache C-arrays for blazing fast memory dispatch
        self.__a_px_o = getattr(self.__group_a, "pos_old_x", None)
        self.__a_py_o = getattr(self.__group_a, "pos_old_y", None)
        self.__a_px_n = getattr(self.__group_a, "pos_new_x", None)
        self.__a_py_n = getattr(self.__group_a, "pos_new_y", None)
        self.__a_sx = getattr(self.__group_a, "size_x", None)
        self.__a_sy = getattr(self.__group_a, "size_y", None)

        self.__b_px_o = getattr(self.__group_b, "pos_old_x", None)
        self.__b_py_o = getattr(self.__group_b, "pos_old_y", None)
        self.__b_px_n = getattr(self.__group_b, "pos_new_x", None)
        self.__b_py_n = getattr(self.__group_b, "pos_new_y", None)
        self.__b_sx = getattr(self.__group_b, "size_x", None)
        self.__b_sy = getattr(self.__group_b, "size_y", None)

    def calculate_collisions(self) -> None:
        self.__collision_func(
            self.__group_a, self.__group_b,
            self.__list_a, self.__list_b, self.__grid_b,
            self.__a_px_o, self.__a_py_o, self.__a_px_n, self.__a_py_n, self.__a_sx, self.__a_sy,
            self.__b_px_o, self.__b_py_o, self.__b_px_n, self.__b_py_n, self.__b_sx, self.__b_sy,
            self.__callback_a, self.__callback_b
        )