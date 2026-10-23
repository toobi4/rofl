"""Hamming(7,4) forward error correction: every nibble earns three parity bits."""

from __future__ import annotations


def encode_nibble(d: int) -> list[int]:
    d1, d2, d3, d4 = (d >> 3) & 1, (d >> 2) & 1, (d >> 1) & 1, d & 1
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return [p1, p2, d1, p3, d2, d3, d4]


def decode_codeword(bits: list[int]) -> tuple[int, bool]:
    b = list(bits)
    s1 = b[0] ^ b[2] ^ b[4] ^ b[6]
    s2 = b[1] ^ b[2] ^ b[5] ^ b[6]
    s3 = b[3] ^ b[4] ^ b[5] ^ b[6]
    syndrome = s1 | s2 << 1 | s3 << 2
    if syndrome:
        b[syndrome - 1] ^= 1
    return b[2] << 3 | b[4] << 2 | b[5] << 1 | b[6], bool(syndrome)


def encode(data: bytes) -> list[list[int]]:
    words = []
    for byte in data:
        words.append(encode_nibble(byte >> 4))
        words.append(encode_nibble(byte & 0xF))
    return words


def decode(words: list[list[int]]) -> tuple[bytes, int]:
    out, corrected = bytearray(), 0
    for high, low in zip(words[0::2], words[1::2]):
        h, ch = decode_codeword(high)
        l, cl = decode_codeword(low)
        corrected += ch + cl
        out.append(h << 4 | l)
    return bytes(out), corrected
