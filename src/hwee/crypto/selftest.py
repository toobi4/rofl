"""Power-on cryptographic self tests (Known Answer Tests).

The reference implementations from the standard library are consulted *only*
here, as an untrusted second opinion, never on the data path.
"""

from __future__ import annotations

import hashlib
import zlib

from hwee.crypto.crc32 import crc32
from hwee.crypto.sha256 import sha256
from hwee.kernel.errors import SelfTestFailure

_VECTORS = [b"", b"abc", b"enterprise" * 17, bytes(range(256)) * 3]


def run_known_answer_tests() -> int:
    passed = 0
    for vector in _VECTORS:
        if sha256(vector) != hashlib.sha256(vector).digest():
            raise SelfTestFailure(f"SHA-256 KAT failed for vector of length {len(vector)}")
        if crc32(vector) != zlib.crc32(vector):
            raise SelfTestFailure(f"CRC-32 KAT failed for vector of length {len(vector)}")
        passed += 2
    return passed
