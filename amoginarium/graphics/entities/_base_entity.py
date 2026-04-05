"""
_base_entity.py
29.03.2026

Graphics base entity

Author:
Nilusink
"""
from __future__ import annotations
import typing as tp


class BaseGraphicsEntity:
    __slots__ = [
        "__g", "_children", "_parent", "_root_visibility", "_highlight",
        "_visible"
    ]

    _cid: str = ...

    _visible: bool
    _parent: tp.Self | None
    _children: list[tp.Self]

    def __init__(self, parent: tp.Self | None = None) -> None:
        try:  # ui implements visible as property without setter
            self._visible = True

        except AttributeError:
            pass

        # pygame groups
        self.__g = []

        self._parent = parent
        self._children = []
        self._root_visibility = False
        self._highlight = False

    # region properties
    @property
    def visible(self) -> bool:
        """
        returns current visibility state
        """
        return self._visible

    @property
    def parent(self) -> BaseGraphicsEntity:
        return self._parent

    # endregion

    # region Methods: pygame
    def add(self, *groups) -> None:
        """
        add entity to one or more groups
        """
        has = self.__g.__contains__

        for group in groups:
            if not has(group):
                group.add_internal(self)
                self.__g.append(group)

    def remove(self, *groups) -> None:
        """
        remove entity from one or more groups
        """
        has = self.__g.__contains__

        for group in groups:
            if has(group):
                group.remove_internal(self)
                self.__g.remove(group)

    def kill(self) -> None:
        """
        remove entity from all groups
        """
        # kill children first
        for child in self._children:
            child.kill()

        # commit suicide
        for group in self.__g:
            group.remove_internal(self)

        self.__g.clear()

    # endregion

    # region class methods
    @classmethod
    def cid(cls) -> str:
        if cls._cid is ...:
            raise ValueError("__cid is not defined for " + cls.__name__)

        return cls._cid
    # endregion

    # region highlighting
    def highlight(self) -> None:
        self._highlight = True

    def stop_highlight(self) -> None:
        self._highlight = False

    # endregion

    # region gl_draw
    def _gl_draw(self, delta_cal: float, layer: int = 0):
        """
        Draw function for this UI.
        Use in inheritance for the actual drawing
        """
        return

    def _before_gl_draw(self, drawn: bool, layer: int = 0) -> None:
        """
        Called before gl_draw
        :param drawn: Whether the UI-entity will be drawn
        :param layer: what layer the draw function has been called by
        """
        return

    def _after_gl_draw(self, drawn: bool, layer: int = 0) -> None:
        """
        Called after gl_draw
        :param drawn: Whether the UI-entity was drawn
        :param layer: what layer the draw function has been called by
        """
        return

    @tp.final
    def gl_draw(self, delta_cal: float, recursive: bool = True, force_draw: bool = False, layer: int = 0) -> None:
        """
        Draw this UI-entity.
        :param delta_cal: delta used for animation calculations
        :param recursive: Draw the children tree recursively
        :param force_draw: Ignore visibility
        :param layer: what layer the draw function has been called by

        Note: Only overwrite in inheritance for before/after draw updates
        Note: Ignores parent visibility
        """
        draw: bool = force_draw or self.visible
        self._before_gl_draw(draw, layer=layer)

        if draw:
            self._gl_draw(delta_cal, layer=layer)
            if recursive:
                for child in self._children:
                    child.gl_draw(delta_cal, force_draw=(force_draw or self._root_visibility), layer=layer)

        self._after_gl_draw(draw)
    # endregion
