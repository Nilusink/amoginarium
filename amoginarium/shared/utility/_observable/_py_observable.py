"""
amoginarium/shared/utility/_py_observable.py

Project: amoginarium
Created: 12.05.2026
Authors: LukasKrah
"""

import typing as tp
import weakref
import types


class PyObservable[T]:
    """
    A generic observable wrapper that notifies subscribers
    when the internal value changes.
    Uses weak references to prevent memory leaks from stale subscriptions.
    """
    __slots__ = ("_value", "_callbacks", "_seen_refs")

    _value: T
    _callbacks: list[tuple[weakref.ReferenceType, tp.Optional[tp.Callable]]]
    _seen_refs: set[tuple[weakref.ReferenceType, tp.Optional[tp.Callable]]]

    def __init__(self, value: T):
        """
        Initializes the observable with a starting value.
        :param value: The initial value of type T.
        """
        self._value = value
        self._callbacks = []
        self._seen_refs = set()

    def get_value(self) -> T:
        """
        Returns the current value.
        :return: The current value of type T.
        """
        return self._value

    def set_value(self, new_value: T) -> None:
        """
        Updates the value and notifies all active subscribers if the value has changed.
        Complexity: O(N) where N is the number of subscribers.
        :param new_value: The new value to assign.
        """
        old_value = self._value
        self._value = new_value

        if old_value != new_value:
            i = 0
            while i < len(self._callbacks):
                target_ref, func = self._callbacks[i]
                obj = target_ref()

                if obj is not None:
                    if func is not None:
                        func(obj, new_value, old_value)
                    else:
                        obj(new_value, old_value)
                    i += 1
                else:
                    self._seen_refs.discard((target_ref, func))
                    self._callbacks[i] = self._callbacks[-1]
                    self._callbacks.pop()

    def subscribe(self, callback: tp.Callable[[T, T], tp.Any]) -> None:
        """
        Registers a callback to be called when the value changes.
        :param callback: A callable taking (new_value, old_value) as arguments.
        """
        if isinstance(callback, types.MethodType):
            t_ref = weakref.ref(callback.__self__)
            t_func = callback.__func__
        else:
            t_ref = weakref.ref(callback)
            t_func = None

        sig = (t_ref, t_func)
        if sig not in self._seen_refs:
            self._seen_refs.add(sig)
            self._callbacks.append(sig)

    def unsubscribe(self, callback: tp.Callable[[T, T], tp.Any]) -> None:
        """
        Unregisters a previously registered callback.
        :param callback: The callable to remove from the subscription list.
        """
        if isinstance(callback, types.MethodType):
            t_ref = weakref.ref(callback.__self__)
            t_func = callback.__func__
        else:
            t_ref = weakref.ref(callback)
            t_func = None

        sig = (t_ref, t_func)
        if sig in self._seen_refs:
            self._seen_refs.discard(sig)
            self._callbacks.remove(sig)
