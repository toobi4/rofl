"""Cryptographic Preimage Recovery Oracle.

Each code point is recovered by brute-force inversion of a salted, stretched
SHA-256 digest, across a process pool, in an order dictated by a full-period
linear congruential generator.
"""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor

from hwee.crypto.sha256 import stretched_sha256
from hwee.kernel.errors import OracleError
from hwee.kernel.plugins import plugin
from hwee.kernel.telemetry import TELEMETRY
from hwee.oracles.base import GlyphOracle


def preimage(salt: bytes, position: int, candidate: int) -> bytes:
    return salt + position.to_bytes(4, "big") + candidate.to_bytes(4, "big")


def lcg_sequence(modulus: int, multiplier: int, increment: int, seed: int):
    value = seed % modulus
    for _ in range(modulus):
        yield value
        value = (multiplier * value + increment) % modulus


def crack(job: tuple[bytes, int, str, int, dict]) -> tuple[int, int | None, int]:
    salt, position, target_hex, iterations, space = job
    target = bytes.fromhex(target_hex)
    attempts = 0
    for candidate in lcg_sequence(space["modulus"], space["multiplier"], space["increment"], space["seed"]):
        attempts += 1
        if stretched_sha256(preimage(salt, position, candidate), iterations) == target:
            return position, candidate, attempts
    return position, None, attempts


@plugin("oracle", "hash_inversion", priority=30)
class HashInversionOracle(GlyphOracle):
    ARTIFACT = "greeting.digests.json"

    def divine(self) -> list[int]:
        spec = self.resources.read_json(self.ARTIFACT)
        salt = bytes.fromhex(spec["salt"])
        jobs = [(salt, i, digest, spec["iterations"], spec["search_space"])
                for i, digest in enumerate(spec["digests"])]
        workers = self.setting("workers", int, 0) or os.cpu_count() or 1
        if workers == 1:
            outcomes = list(map(crack, jobs))
        else:
            with ProcessPoolExecutor(max_workers=workers) as pool:
                outcomes = list(pool.map(crack, jobs))
        result = [0] * len(jobs)
        for position, candidate, attempts in outcomes:
            TELEMETRY.incr("crypto.preimage.attempts", attempts)
            if candidate is None:
                raise OracleError(f"Search space exhausted for position {position}")
            result[position] = candidate
        return result
