# _cy_observable.pyi
import typing as tp

T = tp.TypeVar("T")


class CyObservable(tp.Generic[T]):
    __orig_class__: tp.Any

    def __init__(self, value: T) -> None: ...

    def get_value(self) -> T: ...

    def set_value(self, new_value: T) -> None: ...

    def subscribe(self, callback: tp.Callable[[T, T], tp.Any]) -> None: ...

    def unsubscribe(self, callback: tp.Callable[[T, T], tp.Any]) -> None: ...
