"""Deterministic Entropy Service (xorshift64*).

Randomness is far too important to be left to the standard library.
"""

from __future__ import annotations

_MASK64 = (1 << 64) - 1


class DeterministicEntropySource:
    def __init__(self, seed: int) -> None:
        self._state = (seed * 0x9E3779B97F4A7C15 + 0xD1B54A32D192ED03) & _MASK64 or 1

    def next_u64(self) -> int:
        x = self._state
        x ^= (x >> 12)
        x ^= (x << 25) & _MASK64
        x ^= (x >> 27)
        self._state = x
        return (x * 0x2545F4914F6CDD1D) & _MASK64

    def below(self, bound: int) -> int:
        if bound <= 0:
            raise ValueError("bound must be positive")
        threshold = ((1 << 64) - bound) % bound
        while True:
            value = self.next_u64()
            if value >= threshold:
                return value % bound

    def uniform(self) -> float:
        return (self.next_u64() >> 11) / float(1 << 53)

    def chance(self, probability: float) -> bool:
        return self.uniform() < probability

    def fork(self, label: str) -> "DeterministicEntropySource":
        salt = 0
        for ch in label:
            salt = (salt * 131 + ord(ch)) & _MASK64
        return DeterministicEntropySource(self.next_u64() ^ salt)
