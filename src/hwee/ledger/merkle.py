"""Merkle tree root computation (Bitcoin-style odd-leaf duplication)."""

from __future__ import annotations

import json

from hwee.crypto.sha256 import sha256


def leaf_hash(transaction: dict) -> bytes:
    return sha256(b"\x00" + json.dumps(transaction, sort_keys=True).encode())


def merkle_root(transactions: list[dict]) -> str:
    level = [leaf_hash(tx) for tx in transactions] or [sha256(b"")]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [sha256(b"\x01" + level[i] + level[i + 1]) for i in range(0, len(level), 2)]
    return level[0].hex()
