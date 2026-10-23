"""Blocks and their headers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from hwee.crypto.sha256 import sha256


@dataclass
class Block:
    index: int
    previous_hash: str
    timestamp: int
    merkle_root: str
    difficulty: int
    nonce: int = 0
    transactions: list[dict] = field(default_factory=list)

    def header(self) -> bytes:
        return json.dumps({"index": self.index, "prev": self.previous_hash, "ts": self.timestamp,
                           "merkle": self.merkle_root, "bits": self.difficulty, "nonce": self.nonce},
                          sort_keys=True, separators=(",", ":")).encode()

    def hash(self) -> str:
        return sha256(sha256(self.header())).hex()

    def satisfies_work(self) -> bool:
        return int(self.hash(), 16) < 1 << (256 - self.difficulty)
