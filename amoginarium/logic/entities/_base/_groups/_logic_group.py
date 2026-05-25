"""
Defines the base LogicGroup class for managing collections of logic entities.

Allows batch operations like updates and efficient membership testing.

| ``Path``: amoginarium/logic/entities/_base/_groups/_logic_group.py
| ``Project``: amoginarium
| ``Created``: 21.04.2026
| ``Authors``: Nilusink, LukasKrah
"""

from __future__ import annotations

import contextlib
import typing as tp

from amoginarium.shared import BaseLogicEntityLike


class LogicGroup[T: BaseLogicEntityLike]:
    """
    A container for T objects to facilitate batch updates and management.
    """

    __slots__ = ("_entities",)

    _entities: dict[T, None]

    def __init__(self, *entities: T) -> None:
        """
        Initialize the group with an optional sequence of entities.
        :param entities: Initial entities to add to the group.
        """
        self._entities = dict.fromkeys(entities)

    def entities(self) -> list[T]:
        """:return: A shallow copy of the internal entity list."""
        return list(self._entities.keys())

    def add(self, entity: T) -> None:
        """
        Adds an entity to the group if it is not already present.
        :param entity: The logic entity to add.
        """
        self._entities[entity] = None

    add_internal = add

    def remove(self, entity: T) -> None:
        """
        Removes an entity from the group if it exists.
        :param entity: The logic entity to remove.
        """
        with contextlib.suppress(KeyError):
            del self._entities[entity]

    remove_internal = remove

    def has(self, entity: T) -> bool:
        """
        Checks if the entity is a member of this group.
        :param entity: The logic entity to check.
        :return: True if present, False otherwise.
        """
        return entity in self._entities

    def copy(self) -> LogicGroup:
        """
        Creates a new group containing the same entities.
        :return: A new LogicGroup instance.
        """
        new_group: LogicGroup = self.__class__()
        new_group._entities = self._entities.copy()
        return new_group

    def __iter__(self) -> tp.Iterator[T]:
        """:return: An iterator over the entities in the group."""
        return iter(self._entities)

    def __contains__(self, entity: T) -> bool:
        """
        Membership check for the 'in' operator.
        :param entity: The logic entity to check.
        :return: True if present, False otherwise.
        """
        return entity in self._entities

    def has_any(self, *sprites: T) -> bool:
        """
        Checks if any of the provided entities are in this group.
        :param sprites: Logic entities to check.
        :return: True if at least one entity is present.
        """
        return not self._entities.keys().isdisjoint(sprites)

    def update(self, *args: tp.Any, **kwargs: tp.Any) -> None:
        """
        Batch update all entities in the group.

        :param args: Positional arguments passed to entity.update.
        :param kwargs: Keyword arguments passed to entity.update.
        """
        entity: T
        for entity in self._entities.copy():
            entity.update(*args, **kwargs)

    def empty(self) -> None:
        """Remove all entities from the group."""
        self._entities.clear()

    def __bool__(self) -> bool:
        """:return: True if the group is not empty."""
        return bool(self._entities)

    def __len__(self) -> int:
        """:return: The number of entities in the group."""
        return len(self._entities)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({len(self)} entities)>"
