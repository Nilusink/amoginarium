"""
Dynamically shares debugging data across Processes.

| ``Path``: amoginarium/shared/debugging/_dynamic_memory_allocator/
    _dynamic_shared_debugging.py
| ``Project``: amoginarium
| ``Created``: 25.05.2026
| ``Authors``: Nilusink
"""
from __future__ import annotations

import typing as tp
import ctypes

from icecream import ic

if tp.TYPE_CHECKING:
    from ._callocator_interface import SharedHeap


class SharedDebuggingInstance:
    """Instance of shared debugging variables."""

    def __init__(
        self,
        sh: SharedHeap,
        variable_scheme: list[tuple[str, type[ctypes.c_int]]],
        console_lines: int,
        max_console_line_length: int = 32
    ) -> None:
        """
        Create shared debugging instance.

        :param sh: shared heap (from pv)
        :param variable_scheme: variables, structure: [(<var_name>, <var_ctype>)]
        """
        self.__sh = sh
        self._variable_scheme = variable_scheme
        self._console_lines = console_lines
        self._max_console_line_length = max_console_line_length
        self._offset = -1

    def create(self) -> None:
        """Create required memory."""
        required_size = 0

        # add required variable size
        for _, var_type in self._variable_scheme:
            required_size += ctypes.sizeof(var_type)

        ic(required_size)

        # add required console size
        required_size += self._console_lines * self._max_console_line_length

        ic("f", required_size)

        # allocate
        self._offset = self.__sh.alloc(required_size)

    def write_from_object(self, obj: object) -> None:
        """Write variable scheme from given object."""

        curr_pos = 0
        for var_name, var_type in self._variable_scheme:
            val = getattr(obj, var_name, None)
            data = bytes(var_type(val))

            self.__sh.write(
                self._offset + curr_pos,
                data
            )

            curr_pos += ctypes.sizeof(var_type)

    def read(self) -> None:
        curr_pos = 0
        for var_name, var_type in self._variable_scheme:
            size = ctypes.sizeof(var_type)

            data = self.__sh.read(self._offset + curr_pos, size)
            print(var_name, var_type.from_buffer_copy(data))

            curr_pos += size

    def kill(self) -> None:
        """Close memory."""
        self.__sh.free(self._offset)

    def __del__(self) -> None:
        self.kill()
