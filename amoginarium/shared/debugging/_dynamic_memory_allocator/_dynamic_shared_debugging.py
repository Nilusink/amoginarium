"""
Dynamically shares debugging data across Processes.

| ``Path``: amoginarium/shared/debugging/_dynamic_memory_allocator/
    _dynamic_shared_debugging.py
| ``Project``: amoginarium
| ``Created``: 25.05.2026
| ``Authors``: Nilusink
"""

from __future__ import annotations

import struct
import typing as tp
from functools import reduce

from icecream import ic

from ._data_conversion import from_bytes, sizeof, to_bytes

if tp.TYPE_CHECKING:
    from ._callocator_interface import SharedHeap


class SharedDebuggingInstance:
    """
    Instance of shared debugging variables.

    :ivar __sh: SharedHeap instance
    :ivar _variable_scheme: list of
        [(<var_name>, <var_type> | (<var_type>, <padding: int>), ...]
    :ivar _console_lines: max n of console lines
    :ivar _max_console_line_length: max length of one console line
    :ivar _offset: memory starting offset
    :ivar _allocated_size: size of allocated heap in bytes
    :ivar _var_sizes: byte sizes of var_scheme
    """

    # region InstanceVars
    __sh: SharedHeap
    _variable_scheme: list[tuple[str, type | tuple[type, int]]]
    _console_lines: int
    _max_console_line_length: int
    _offset: int
    _allocated_size: int
    # endregion

    def __init__(
        self,
        sh: SharedHeap,
        variable_scheme: list[tuple[str, type | tuple[type, int]]],
        console_lines: int,
        max_console_line_length: int = 32,
    ) -> None:
        """
        Create shared debugging instance.

        :param sh: shared heap (from pv)
        :param variable_scheme: variables, structure:
            [(<var_name>, <var_type> | (<var_type>, <padding: int>), ...]
        """
        self.__sh = sh
        self._variable_scheme = variable_scheme
        self._console_lines = console_lines
        self._max_console_line_length = max_console_line_length
        self._offset = -1
        self._allocated_size = -1
        self._console_offset = -1
        self._var_sizes = []
        self._current_char = 0

    # region properties
    @property
    def offset(self) -> int:
        """:return: offset, -1 if not set."""
        if self._offset < 0:
            self.create()

        return self._offset

    @property
    def max_console_line_length(self) -> int:
        """:return: max length of console lines."""
        return self._max_console_line_length

    @property
    def console_lines(self) -> int:
        """:return: amount of console lines."""
        return self._console_lines

    # endregion

    # region initialization
    def get_spawn_data(self) -> dict[str, tp.Any]:
        """
        :return: All data required for graphics spawn
        """
        return {
            "off": self._offset,
            "var_scheme": self._variable_scheme,
            "var_sizes": self._var_sizes,
            "console_lines": self._console_lines,
            "max_console_line_length": self._max_console_line_length,
            "allocated_size": self._allocated_size,
            "console_offset": self._console_offset,
        }

    def create(self) -> None:
        """Create required memory."""
        required_size = 0

        # add required variable size
        for _, var_type in self._variable_scheme:
            if isinstance(var_type, tuple):
                size = sizeof(var_type[0](), pad_size=var_type[1])

            else:
                size = sizeof(var_type())

            required_size += size
            self._var_sizes.append(size)

        # add required console size
        required_size += 2  # add two bytes for curr terminal pos
        self._console_offset = required_size
        required_size += self._console_lines * self._max_console_line_length

        # allocate
        self._offset = self.__sh.alloc(required_size)
        self._allocated_size = required_size

    @classmethod
    def from_data(cls, sh: SharedHeap, data: dict[str, tp.Any]) -> tp.Self:
        instance = cls(
            sh=sh,
            variable_scheme=data["var_scheme"],
            console_lines=data["console_lines"],
            max_console_line_length=data["max_console_line_length"],
        )

        instance._offset = data["off"]
        instance._allocated_size = data["allocated_size"]
        instance._var_sizes = data["var_sizes"]
        instance._console_offset = data["console_offset"]

        return instance

    # endregion

    # region runtime interface
    def write_from_object(self, obj: object) -> None:
        """Write variable scheme from given object."""
        curr_pos = 0
        for (var_name, var_type), var_size in zip(
            self._variable_scheme, self._var_sizes, strict=True
        ):
            if "." in var_name:
                val = reduce(
                    lambda a, b: getattr(a, b, None),
                    var_name.split("."),
                    obj,
                )

            else:
                val = getattr(obj, var_name, None)

            if val is None:
                curr_pos += var_size
                continue

            padding = var_type[1] if isinstance(var_type, tuple) else -1
            data = to_bytes(val, pad_size=padding)

            self.__sh.write(self._offset + curr_pos, data)

            curr_pos += var_size

    def read(self) -> dict[str, tp.Any]:
        curr_pos = 0

        out = {}
        for (var_name, var_type), var_size in zip(
            self._variable_scheme, self._var_sizes, strict=True
        ):
            # read data
            data = self.__sh.read(self._offset + curr_pos, var_size)

            # convert data
            d_type = var_type[0] if isinstance(var_type, tuple) else var_type
            out[var_name] = from_bytes(data, d_type)

            # increment reader position
            curr_pos += var_size

        return out

    def print(self, text: str, *, end: str = "\n") -> None:
        """
        Print text to the terminal.

        :param text: text to print to terminal
        :param end: character to append to end of text
        """
        text += end

        for character in text.encode("utf-8"):
            self.__sh.write_byte(
                self._offset + self._console_offset + self._current_char,
                character,
            )

            # wrap around at end of terminal (ring buffer)
            self._current_char = (self._current_char + 1) % (
                self._console_lines * self._max_console_line_length
            )

        # write current cursor pos to buffer
        self.__sh.write(
            self._offset + self._console_offset - 2,
            struct.pack("<H", self._current_char),  # treat as unsigned short
        )

    def get_console_lines(self) -> str:
        """:return: console lines."""
        out: list[str] = []

        current_write_pos = struct.unpack(
            "<H", self.__sh.read(self._offset + self._console_offset - 2, 2)
        )[0]

        for i in range(self._console_lines * self._max_console_line_length):
            val: int = self.__sh.read_byte(self._offset + self._console_offset + i)

            # append character to char array
            out.append(chr(val))

        # re-sort list based on current index and convert to string
        return "".join(
            character
            for character in out[current_write_pos:] + out[:current_write_pos]
            if character != "\0"
        )

    def kill(self) -> None:
        """Close memory."""
        self.__sh.free(self._offset)

    # endregion
