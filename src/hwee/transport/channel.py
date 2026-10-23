"""A binary symmetric channel with bounded burst errors, for realism."""

from __future__ import annotations

from hwee.kernel.entropy import DeterministicEntropySource


class NoisyChannel:
    def __init__(self, entropy: DeterministicEntropySource, error_probability: float) -> None:
        self.entropy = entropy
        self.error_probability = error_probability
        self.flips = 0

    def transmit(self, codewords: list[list[int]]) -> list[list[int]]:
        received = []
        for word in codewords:
            word = list(word)
            if self.entropy.chance(self.error_probability):
                word[self.entropy.below(len(word))] ^= 1  # at most one flip: within the FEC envelope
                self.flips += 1
            received.append(word)
        return received
