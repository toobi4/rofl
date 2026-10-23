"""RFC 4648 Base64, with the alphabet generated rather than typed."""

from __future__ import annotations

from hwee.kernel.errors import TransportError

ALPHABET = "".join(map(chr, [*range(65, 91), *range(97, 123), *range(48, 58)])) + "+/"
_REVERSE = {ch: i for i, ch in enumerate(ALPHABET)}


def encode(data: bytes) -> str:
    out = []
    for i in range(0, len(data), 3):
        chunk = data[i:i + 3]
        n = int.from_bytes(chunk.ljust(3, b"\0"), "big")
        quad = "".join(ALPHABET[(n >> s) & 63] for s in (18, 12, 6, 0))
        out.append(quad[:len(chunk) + 1] + "=" * (3 - len(chunk)))
    return "".join(out)


def decode(text: str) -> bytes:
    if len(text) % 4:
        raise TransportError("Base64 length must be a multiple of four")
    out = bytearray()
    for i in range(0, len(text), 4):
        quad = text[i:i + 4]
        pad = quad.count("=")
        n = 0
        for ch in quad.rstrip("="):
            if ch not in _REVERSE:
                raise TransportError(f"Invalid Base64 character {ch!r}")
            n = n << 6 | _REVERSE[ch]
        n <<= 6 * pad
        out += n.to_bytes(3, "big")[:3 - pad]
    return bytes(out)
