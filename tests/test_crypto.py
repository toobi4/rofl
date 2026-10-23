import hashlib
import unittest
import zlib

from hwee.crypto.crc32 import crc32
from hwee.crypto.number_theory import first_primes, integer_root
from hwee.crypto.sha256 import H0, sha256


class CryptoTests(unittest.TestCase):
    def test_constants_match_fips_180_4(self):
        self.assertEqual(H0[0], 0x6A09E667)
        self.assertEqual(H0[7], 0x5BE0CD19)

    def test_sha256_matches_reference(self):
        for n in (0, 1, 55, 56, 64, 119, 1000):
            data = bytes(range(256)) * 4
            self.assertEqual(sha256(data[:n]), hashlib.sha256(data[:n]).digest())

    def test_crc32_matches_reference(self):
        self.assertEqual(crc32(b"enterprise"), zlib.crc32(b"enterprise"))

    def test_number_theory(self):
        self.assertEqual(first_primes(5), [2, 3, 5, 7, 11])
        self.assertEqual(integer_root(10 ** 30 + 5, 3), 10 ** 10)
