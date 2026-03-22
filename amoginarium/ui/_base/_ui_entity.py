"""
amoginarium/ui/_base/_ui_entity.py

Project: amoginarium
Created: 10.03.2026
Authors: LukasKrah
"""

from __future__ import annotations

import typing as tp
if tp.TYPE_CHECKING:
    from ._ui_element import UIElement

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
    def _reset(self) -> None:
        """Reset the UI-Entity. Use in inheritance for actual resetting"""
        return

    def reset(self, recursive: bool = True) -> None:
        """
        Reset the UI-Entity and all its children recursively
        :param recursive: Also reset the children tree recursively
        """
        self._reset()
        if recursive:
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

    def _set_visibility_recursive(
            self,
            value: bool | None,
            is_caller: bool = False,
    ) -> None:
        """
        Set the visibility of this UI-Entity and all its children recursively. Not intended for external use.
        :param value: New visibility
        :param is_caller: Will not affect the visibility attributes of this UI-Entity
        """
        if not is_caller:
            self._visible = value
            self._root_visibility = False
        for child in self._children:
            child._set_visibility_recursive(value)

    def __set_visibility(self, value: bool | None, recursive: bool = False, attach_to_parent: bool = True) -> None:
        """
        Set visibility of this UI-Entity.
        :param recursive: Whether to overwrite the visibility down the children tree
        :param attach_to_parent: Whether to attach the visibility of the children tree to this UI-Entity.
                                 If False, the visibility of each child is individually set to hide
                                 Only used if recursive is set to True.
        """
        self._destroy_root_visibility()

        self._visible = value

        if not recursive:
            if not self._root_visibility:
                self.__check_root_visibility()
        else:
            if attach_to_parent:
                if not self._root_visibility:
                    self._set_visibility_recursive(None, is_caller=True)
                    self._root_visibility = True
            else:
                self._set_visibility_recursive(value, is_caller=True)

    def hide(self, recursive: bool = False, attach_to_parent: bool = True, reset: bool = True) -> None:
        """
        Hide this UI-Entity. By default, the children tree is attached to this visibility.
        :param recursive: Whether to overwrite the visibility down the children tree
        :param attach_to_parent: Whether to attach the visibility of the children tree to this UI-Entity.
                                 If False, the visibility of each child is individually set to hide
                                 Only used if recursive is set to True.
        :param reset: Whether reset should be called recursively
        """
        self.__set_visibility(False, recursive=recursive, attach_to_parent=attach_to_parent)
        if reset:
            self.reset()

    def show(self, recursive: bool = False, attach_to_parent: bool = True, reset: bool = False) -> None:
        """
        Show this UI-Entity. By default, the children tree is attached to this visibility.
        :param recursive: Whether to overwrite the visibility down the children tree
        :param attach_to_parent: Whether to attach the visibility of the children tree to this UI-Entity.
                                 If False, the visibility of each child is individually set to show
                                 Only used if recursive is set to True.
        :param reset: Whether reset should be called recursively
        """
        self.__set_visibility(True, recursive=recursive, attach_to_parent=attach_to_parent)
        if reset:
            self.reset()

    def set_visibility(
            self,
            value: bool | None,
            recursive: bool = False,
            attach_to_parent: bool = True,
            reset: bool = ...
    ) -> None:
        """
        Set the visibility of this UI-Entity.
        :param value: New visibility. None means attach to the next parent visibility
        :param recursive: Whether to overwrite the visibility down the children tree
        :param attach_to_parent: Whether to attach the visibility of the children tree to this UI-Entity.
                                 If False, the visibility of each child is individually set to show
                                 Only used if recursive is set to True.
        :param reset: Whether reset should be called recursively. Defaults to True if value is False, False otherwise.
        """
        self.__set_visibility(value, recursive=recursive, attach_to_parent=attach_to_parent)
        reset = reset if reset is not ... else (value is False)
        if reset:
            self.reset()

    # endregion

    # region Methods: drawing
    def _gl_draw(self) -> None:
        """
        Draw function for this UI.
        Use in inheritance for the actual drawing
        """
        return

    def gl_draw(self, recursive: bool = True, force_draw: bool = False) -> None:
        """
        Draw this UI-entity.
        :param recursive: Draw the children tree recursively
        :param force_draw: Ignore visibility

        Note: Only overwrite in inheritance for before/after draw updates
        Note: Ignores parent visibility
        """
        if force_draw or self.visible:
            self._gl_draw()
            if recursive:
                for child in self._children:
                    child.gl_draw(force_draw=(force_draw or self._root_visibility))

    # endregion

    # region Methods: update
    def _update(self, delta: float) -> None:
        """
        Actual update function for this UI-Entity.
        Use in inheritance for the actual updating.
        :param delta: Time since the last update in seconds
        """
        return

    def update(self, delta: float, recursive: bool = True) -> None:
        """
        Update ui entity
        :param delta: Time since the last update in seconds
        :param recursive: Update the children tree recursively
        """
        self.update(delta)
        if recursive:
            for child in self._children:
                child.update(delta)

    # endregion

    # region Methods: ui-element
    @property
    def _next_ui_element_parent(self) -> UIElement | None:
        if self._parent is not None:
            return self._parent if self._parent._is_ui_element else self._parent._next_ui_element_parent
        return None

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
