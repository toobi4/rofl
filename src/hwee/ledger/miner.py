"""Proof-of-work miner."""

from __future__ import annotations

from hwee.kernel.telemetry import TELEMETRY
from hwee.ledger.block import Block


class Miner:
    def mine(self, block: Block) -> Block:
        block.nonce = 0
        while not block.satisfies_work():
            block.nonce += 1
        TELEMETRY.incr("ledger.hashes_mined", block.nonce + 1)
        return block
