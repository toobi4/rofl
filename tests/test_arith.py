import unittest

from hwee.arith.bigint import BigInt
from hwee.arith.bignat import BigNat
from hwee.logic.circuits import full_adder


class ArithmeticTests(unittest.TestCase):
    def test_full_adder_truth_table(self):
        for a in (0, 1):
            for b in (0, 1):
                for c in (0, 1):
                    total, carry = full_adder(a, b, c)
                    self.assertEqual(total + 2 * carry, a + b + c)

    def test_bignat_roundtrip_and_division(self):
        a, b = BigNat.from_decimal("98765432109876543210"), BigNat.from_decimal("12345")
        q, r = divmod(a, b)
        self.assertEqual((q.to_python_int(), r.to_python_int()), divmod(98765432109876543210, 12345))

    def test_bigint_signs(self):
        for x, y in [(-7, 3), (7, -3), (-7, -3), (0, 5)]:
            a, b = BigInt.from_decimal(str(x)), BigInt.from_decimal(str(y))
            self.assertEqual((a + b).to_python_int(), x + y)
            self.assertEqual((a - b).to_python_int(), x - y)
            self.assertEqual((a * b).to_python_int(), x * y)
