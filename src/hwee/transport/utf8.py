"""RFC 3629 UTF-8 codec, because str.encode() is a black box."""

from __future__ import annotations

from hwee.kernel.errors import TransportError


def encode(code_points: list[int]) -> bytes:
    out = bytearray()
    for cp in code_points:
        if cp < 0 or cp > 0x10FFFF or 0xD800 <= cp <= 0xDFFF:
            raise TransportError(f"Invalid scalar value {cp:#x}")
        if cp < 0x80:
            out.append(cp)
        elif cp < 0x800:
            out += bytes((0xC0 | cp >> 6, 0x80 | cp & 0x3F))
        elif cp < 0x10000:
            out += bytes((0xE0 | cp >> 12, 0x80 | cp >> 6 & 0x3F, 0x80 | cp & 0x3F))
        else:
            out += bytes((0xF0 | cp >> 18, 0x80 | cp >> 12 & 0x3F, 0x80 | cp >> 6 & 0x3F, 0x80 | cp & 0x3F))
    return bytes(out)


def decode(data: bytes) -> list[int]:
    result, i = [], 0
    while i < len(data):
        lead = data[i]
        if lead < 0x80:
            length, cp = 1, lead
        elif lead >> 5 == 0b110:
            length, cp = 2, lead & 0x1F
        elif lead >> 4 == 0b1110:
            length, cp = 3, lead & 0x0F
        elif lead >> 3 == 0b11110:
            length, cp = 4, lead & 0x07
        else:
            raise TransportError(f"Invalid UTF-8 lead byte {lead:#x}")
        for continuation in data[i + 1:i + length]:
            if continuation >> 6 != 0b10:
                raise TransportError("Invalid UTF-8 continuation byte")
            cp = cp << 6 | continuation & 0x3F
        result.append(cp)
        i += length
    return result
