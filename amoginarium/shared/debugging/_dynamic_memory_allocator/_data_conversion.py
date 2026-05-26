"""
Converts data into bytes and back.
"""

from types import EllipsisType
import typing as tp
import struct

from icecream import ic

from amoginarium.shared.utility import Vec2


def to_bytes(data: tp.Any, *, pad_size: int = -1) -> bytes:  # noqa: PLR0911
    """
    Convert data to bytes.

    :param data: Data to be converted
    :param pad_size: Data padding length, only applicable for strings and lists
    :return: Byte data
    """
    dtype = type(data)

    if dtype is bytes:
        return data

    if dtype is int:
        return struct.pack("<q", data)  # convert to 64 bit int

    if dtype is float:
        return struct.pack("<d", data)  # convert to double

    if dtype is bool:
        return struct.pack("<?", data)

    if dtype is str:
        b_data = data.encode("utf-8")

        # pad to max_size
        if len(b_data) > pad_size:
            b_data = b_data[:pad_size]

        else:
            b_data += b"\0" * (pad_size - len(b_data))

        return b_data

    if dtype is Vec2:
        return bytes(data)

    if dtype is list or dtype is tuple:
        conv_data = [to_bytes(e) for e in data]

        if len(conv_data) > pad_size:
            conv_data = conv_data[:pad_size]

        else:
            conv_data += [b"\0" * len(conv_data[0])] * (pad_size - len(conv_data))

        return b"".join(conv_data)

    return b""


def sizeof(data: tp.Any, *, pad_size: int = -1) -> int:
    """
    Get byte size of data.

    Shortcut for:
    ::
        len(to_bytes(data))

    :param data: Data to be converted
    :param pad_size: Data padding length, only applicable for strings and lists
    :return: Byte data
    """
    return len(to_bytes(data, pad_size=pad_size))


def from_bytes[A](  # noqa: PLR0911
        data: bytes,
        dtype: A,
        *,
        element_type: type = EllipsisType,
) -> A:
    """
    Convert bytes to a data type.

    :param data: Data to be converted
    :param dtype: Data type
    :param element_type: Element data type (lists only)
    :return: Converted data
    :raises: ValueError on no element type with list
    """
    if dtype is bytes:
        return data

    if dtype is int:
        return struct.unpack("<q", data)[0]

    if dtype is float:
        return struct.unpack("<d", data)[0]

    if dtype is bool:
        return struct.unpack("<?", data)[0]

    if dtype is str:
        # get string length by finding null terminator
        d_length = data.find(b"\0")

        # if not found, return whole block as data
        if d_length == -1:
            d_length = len(data)

        return data[:d_length].decode("utf-8")

    if dtype is Vec2:
        return Vec2().from_bytes(data)

    if dtype is list or dtype is tuple:
        if element_type is EllipsisType:
            msg = "Element type specifier needed for list"
            raise ValueError(msg)

        e_size = sizeof(element_type())
        o_data = [
            from_bytes(data[i : i + e_size], element_type)
            for i in range(0, len(data), e_size)
        ]

        return dtype(o_data)

    return dtype()


if __name__ == "__main__":
    var = Vec2().from_polar(1, 34)

    b_data = to_bytes(var, pad_size=16)
    ic(b_data, len(b_data))
    c_data = from_bytes(b_data, type(var))
    ic(c_data)
