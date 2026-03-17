"""
amoginarium/ui/_base/_ui_entity.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp

from amoginarium.entities import BaseEntity


class UIEntity(BaseEntity):
    """Base UI-Entity, no UI, just default entity relation / method stuff"""
    _parent: UIEntity | None
    _children: list[UIEntity]

    _visible: bool | None
    _root_visibility: bool
    __visibility_change_root: bool

    __is_ui_element: bool

    def __init__(
            self,
            parent: UIEntity | None = None,
            *args: tp.Any,
            _is_ui_element: bool = False
    ) -> None:
        """
        Create base UI-Entity
        :param parent: Optional parent UI-Entity
        """
        super().__init__(parent)

        self._children = []
        self._visible = None  # Default visibility is attach to next parent visibility
        self._root_visibility = False
        self.__visibility_change_root = False
        self.__is_ui_element = _is_ui_element

        if parent is not None:
            parent.add_child(self)

    # region Methods: children
    def add_child(self, child: UIEntity) -> None:
        """
        Add a child UI-Entity to this UI-Entity
        :param child: Child UI-Entity
        """
        if child not in self._children:
            self._children.append(child)
            child.parent = self

    def remove_child(self, child: UIEntity) -> None:
        """
        Remove a child UI-Entity from this UI-Entity
        :param child: Child UI-Entity
        """
        if child in self._children:
            self._children.remove(child)
            child.parent = None

    # endregion

    # region Methods: reset
    def reset(self) -> None:
        """Reset the UI-Entity"""
        return

    def reset_recursive(self) -> None:
        """Reset the UI-Entity and all its children recursively"""
        self.reset()
        for child in self._children:
            child.reset()

    #endregion

    # region Methods: visibility
    def _destroy_root_visibility(self) -> None:
        """Destroys the root visibility up the parent chain"""
        if self._parent is not None:
            self._parent._root_visibility = False
            self._parent._destroy_root_visibility()

    def __check_root_visibility(self) -> None:
        """Check the children visibility chain to detect if the visibility of this entity is a root visibility"""
        is_root: bool = True
        for child in self._children:
            if child._visible is not None:
                is_root = False
                break
        self._root_visibility = is_root

    def __show(self, is_caller: bool) -> None:
        """Show the UI-Entity"""
        self._visible = True if is_caller else None

    def show(self) -> None:
        """Show the UI-Entity"""
        self._destroy_root_visibility()
        self.__check_root_visibility()
        self.__show(True)

    def _show_recursive_attached(self, is_caller: bool) -> None:
        """Show this UI-Entity and all its children recursively"""
        self.__show(is_caller)
        for child in self._children:
            child._show_recursive_attached(False)

    def show_recursive_attached(self) -> None:
        """Hide this UI-Entity and attach all children to this visibility"""
        self._destroy_root_visibility()
        if self._root_visibility:
            self._visible = True
        else:
            self._show_recursive_attached(True)
        self._root_visibility = True

    def __hide(self, is_caller: bool) -> None:
        """Hide this UI-Entity"""
        self._visible = False if is_caller else None

    def hide(self) -> None:
        """Hide this UI-Entity"""
        self._destroy_root_visibility()
        self.__check_root_visibility()
        self.__hide(True)

    def _hide_recursive_attached(self, is_caller: bool) -> None:
        """Hide this UI-Entity and all its children recursively"""
        self.__hide(is_caller)
        for child in self._children:
            child._hide_recursive_attached(False)

    def hide_recursive_attached(self) -> None:
        """Hide this UI-Entity and attach all children to this visibility"""
        self._destroy_root_visibility()
        if self._root_visibility:
            self._visible = False
        else:
            self._hide_recursive_attached(True)
        self._root_visibility = True

    def _hide_recursive_individual(self) -> None:
        """Hide this UI-Entity and all its children recursively"""
        self.__hide(True)
        for child in self._children:
            child._hide_recursive_individual()

    def hide_recursive_individual(self) -> None:
        """Hide this UI-Entity and all its children recursively"""
        self._destroy_root_visibility()
        self._hide_recursive_individual()

    # endregion

    # region Methods: drawing
    def gl_draw(self) -> None:
        """Draw, that is called by the game loop every frame"""
        return

    def gl_draw_recursive(self) -> None:
        """Draw the UI-Entity and all its children recursively"""
        self.gl_draw()
        for child in self._children:
            child.gl_draw_recursive()

    def draw_if_visible(self) -> None:
        """Draw the UI-Entity if it is visible"""
        if self.visible:
            self.gl_draw()

    def draw_if_visible_recursive(self) -> None:
        """Draw the UI-Entity and all its children recursively"""
        if self.visible:
            if self._root_visibility:
                self.gl_draw_recursive()
            else:
                self.gl_draw()
                for child in self._children:
                    child.draw_if_visible_recursive()

    # endregion

    # region Methods: update
    def update(self, delta: float) -> None:
        """
        Update, that is called by the update loop of the game
        :param delta: Time since the last update in seconds
        """
        return

    def update_recursive(self, delta: float) -> None:
        """
        Update the UI-Entity and all its children recursively
        :param delta: Time since the last update in seconds
        """
        self.update(delta)
        for child in self._children:
            child.update_recursive(delta)

    # endregion

    # region Properties

    @property
    def visible(self) -> bool:
        """:return: Whether the ui entity is visible"""
        parent_vis = False
        if self._parent is not None:
            parent_vis = self._parent.visible
        return self._visible if self._visible is not None else parent_vis

    @property
    def parent(self) -> UIEntity:
        """:return: Parent entity or None"""
        return self._parent

    @parent.setter
    def parent(self, value: UIEntity) -> None:
        """:param value: New parent entity"""
        if value == self._parent:
            return
        if self._parent:
            self._parent.remove_child(self)
        self._parent = value
        if self._parent:
            self._parent.add_child(self)

    @property
    def children(self) -> list[UIEntity]:
        """return: List of children"""
        return self._children

    @property
    def root(self) -> UIEntity:
        """return: Root entity or None"""
        return self._parent.root if self._parent else self

    @property
    def _is_ui_element(self) -> bool:
        """:return: Whether the entity has a size and positon"""
        return self.__is_ui_element

    # endregion
