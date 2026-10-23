"""IEEE 802.3 CRC-32, table generated from the reflected polynomial."""

from __future__ import annotations

_POLY = 0xEDB88320


def _make_table() -> tuple[int, ...]:
    table = []
    for n in range(256):
        c = n
        for _ in range(8):
            c = (c >> 1) ^ _POLY if c & 1 else c >> 1
        table.append(c)
    return tuple(table)


_TABLE = _make_table()


def crc32(data: bytes, value: int = 0) -> int:
    crc = value ^ 0xFFFFFFFF
    for byte in data:
        crc = _TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF
