"""FIPS 180-4 SHA-256 in pure Python, with constants derived at import time."""

from __future__ import annotations

from hwee.crypto.number_theory import first_primes, fractional_bits
from hwee.kernel.telemetry import TELEMETRY

_M = 0xFFFFFFFF
_PRIMES = first_primes(64)
K = tuple(fractional_bits(p, 3) for p in _PRIMES)
H0 = tuple(fractional_bits(p, 2) for p in _PRIMES[:8])


def _rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & _M


def _pad(message: bytes) -> bytes:
    length = len(message) * 8
    padded = message + b"\x80"
    padded += b"\x00" * ((56 - len(padded) % 64) % 64)
    return padded + length.to_bytes(8, "big")


def _compress(state: list[int], block: bytes) -> list[int]:
    w = [int.from_bytes(block[i:i + 4], "big") for i in range(0, 64, 4)]
    for t in range(16, 64):
        x, y = w[t - 15], w[t - 2]
        s0 = _rotr(x, 7) ^ _rotr(x, 18) ^ (x >> 3)
        s1 = _rotr(y, 17) ^ _rotr(y, 19) ^ (y >> 10)
        w.append((w[t - 16] + s0 + w[t - 7] + s1) & _M)
    a, b, c, d, e, f, g, h = state
    for t in range(64):
        s1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
        ch = (e & f) ^ (~e & g)
        t1 = (h + s1 + ch + K[t] + w[t]) & _M
        s0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
        maj = (a & b) ^ (a & c) ^ (b & c)
        t2 = (s0 + maj) & _M
        h, g, f, e, d, c, b, a = g, f, e, (d + t1) & _M, c, b, a, (t1 + t2) & _M
    return [(x + y) & _M for x, y in zip(state, (a, b, c, d, e, f, g, h))]


def sha256(message: bytes) -> bytes:
    TELEMETRY.incr("crypto.sha256.invocations")
    state = list(H0)
    padded = _pad(message)
    for offset in range(0, len(padded), 64):
        state = _compress(state, padded[offset:offset + 64])
    return b"".join(x.to_bytes(4, "big") for x in state)


def sha256_hex(message: bytes) -> str:
    return sha256(message).hex()


def stretched_sha256(message: bytes, iterations: int) -> bytes:
    digest = message
    for _ in range(iterations):
        digest = sha256(digest)
    return digest
