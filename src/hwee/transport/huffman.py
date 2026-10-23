"""Canonical Huffman coding, for compressing a 13-byte payload to roughly 13 bytes."""

from __future__ import annotations

import heapq
import struct
from collections import Counter

from hwee.kernel.errors import TransportError


def _code_lengths(data: bytes) -> dict[int, int]:
    frequencies = Counter(data)
    if len(frequencies) == 1:
        return {next(iter(frequencies)): 1}
    heap = [(count, symbol, (symbol,)) for symbol, count in frequencies.items()]
    heapq.heapify(heap)
    lengths = dict.fromkeys(frequencies, 0)
    while len(heap) > 1:
        c1, k1, s1 = heapq.heappop(heap)
        c2, k2, s2 = heapq.heappop(heap)
        for symbol in s1 + s2:
            lengths[symbol] += 1
        heapq.heappush(heap, (c1 + c2, min(k1, k2), s1 + s2))
    return lengths


def _canonical(lengths: dict[int, int]) -> dict[int, str]:
    codes, code, previous = {}, 0, 0
    for symbol, length in sorted(lengths.items(), key=lambda kv: (kv[1], kv[0])):
        code <<= length - previous
        codes[symbol] = format(code, f"0{length}b")
        code += 1
        previous = length
    return codes


def compress(data: bytes) -> bytes:
    lengths = _code_lengths(data) if data else {}
    codes = _canonical(lengths)
    bits = "".join(codes[b] for b in data)
    padding = (-len(bits)) % 8
    bits += "0" * padding
    header = struct.pack(">IHB", len(data), len(lengths), padding)
    header += b"".join(struct.pack(">BB", s, l) for s, l in sorted(lengths.items()))
    return b"HUF1" + header + bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def decompress(blob: bytes) -> bytes:
    if blob[:4] != b"HUF1":
        raise TransportError("Not a Huffman stream")
    size, symbols, _padding = struct.unpack(">IHB", blob[4:11])
    offset = 11
    lengths = {}
    for _ in range(symbols):
        symbol, length = struct.unpack(">BB", blob[offset:offset + 2])
        lengths[symbol] = length
        offset += 2
    decoder = {code: symbol for symbol, code in _canonical(lengths).items()}
    out, buffer = bytearray(), ""
    for byte in blob[offset:]:
        for bit in format(byte, "08b"):
            buffer += bit
            if buffer in decoder:
                out.append(decoder[buffer])
                buffer = ""
                if len(out) == size:
                    return bytes(out)
    if len(out) != size:
        raise TransportError("Truncated Huffman stream")
    return bytes(out)
