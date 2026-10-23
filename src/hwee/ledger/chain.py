"""The Greeting Ledger."""

from __future__ import annotations

from hwee.kernel.errors import LedgerIntegrityError
from hwee.ledger.block import Block
from hwee.ledger.merkle import merkle_root
from hwee.ledger.miner import Miner

GENESIS_PREVIOUS = "0" * 64


class Blockchain:
    def __init__(self, difficulty: int, miner: Miner) -> None:
        self.difficulty = difficulty
        self.miner = miner
        self.blocks: list[Block] = []
        self._clock = 0
        self.append([{"type": "genesis", "memo": "In the beginning there was boilerplate."}])

    def _tick(self) -> int:
        self._clock += 1  # Lamport clock: wall time is non-deterministic and thus forbidden
        return self._clock

    def append(self, transactions: list[dict]) -> Block:
        previous = self.blocks[-1].hash() if self.blocks else GENESIS_PREVIOUS
        block = Block(len(self.blocks), previous, self._tick(), merkle_root(transactions),
                      self.difficulty, transactions=transactions)
        self.blocks.append(self.miner.mine(block))
        return block

    def validate(self) -> None:
        for index, block in enumerate(self.blocks):
            expected_previous = self.blocks[index - 1].hash() if index else GENESIS_PREVIOUS
            if block.index != index:
                raise LedgerIntegrityError(f"Block {index} has wrong index {block.index}")
            if block.previous_hash != expected_previous:
                raise LedgerIntegrityError(f"Block {index} breaks the hash chain")
            if block.merkle_root != merkle_root(block.transactions):
                raise LedgerIntegrityError(f"Block {index} has a forged Merkle root")
            if not block.satisfies_work():
                raise LedgerIntegrityError(f"Block {index} lacks sufficient proof of work")
            if index and block.timestamp <= self.blocks[index - 1].timestamp:
                raise LedgerIntegrityError(f"Block {index} violates causality")

    def transactions(self, kind: str) -> list[dict]:
        return [tx for block in self.blocks for tx in block.transactions if tx.get("type") == kind]
