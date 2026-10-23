"""Combinational circuits: adders, comparators, inverters.

Bit vectors are little-endian lists of 0/1 integers.
"""

from __future__ import annotations

from hwee.logic.gates import nand, not_, xor


def half_adder(a: int, b: int) -> tuple[int, int]:
    t = nand(a, b)
    return nand(nand(a, t), nand(b, t)), not_(t)


def full_adder(a: int, b: int, carry_in: int) -> tuple[int, int]:
    """The classic nine-NAND full adder."""
    n1 = nand(a, b)
    n2 = nand(a, n1)
    n3 = nand(b, n1)
    n4 = nand(n2, n3)          # a xor b
    n5 = nand(n4, carry_in)
    n6 = nand(n4, n5)
    n7 = nand(carry_in, n5)
    total = nand(n6, n7)       # a xor b xor c
    carry = nand(n5, n1)
    return total, carry


def ripple_carry_adder(a: list[int], b: list[int], carry_in: int = 0) -> tuple[list[int], int]:
    width = max(len(a), len(b))
    a = a + [0] * (width - len(a))
    b = b + [0] * (width - len(b))
    out: list[int] = []
    carry = carry_in
    for bit_a, bit_b in zip(a, b):
        total, carry = full_adder(bit_a, bit_b, carry)
        out.append(total)
    return out, carry


def inverter_bank(bits: list[int]) -> list[int]:
    return [not_(bit) for bit in bits]


def subtractor(a: list[int], b: list[int]) -> tuple[list[int], int]:
    """a - b in two's complement. Returns (difference, no_borrow)."""
    width = max(len(a), len(b))
    a = a + [0] * (width - len(a))
    b = b + [0] * (width - len(b))
    return ripple_carry_adder(a, inverter_bank(b), carry_in=1)


def equality_comparator(a: list[int], b: list[int]) -> int:
    width = max(len(a), len(b))
    a = a + [0] * (width - len(a))
    b = b + [0] * (width - len(b))
    differs = 0
    for bit_a, bit_b in zip(a, b):
        differs = nand(not_(differs), not_(xor(bit_a, bit_b)))
    return not_(differs)
