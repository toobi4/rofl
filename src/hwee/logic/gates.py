"""The universal gate, and everything else expressed in terms of it."""

from __future__ import annotations


class GateCounter:
    nand_evaluations = 0
    votes = 0


def _physical_nand(a: int, b: int) -> int:
    GateCounter.nand_evaluations += 1
    return 0 if (a and b) else 1


def _majority_voter(x: int, y: int, z: int) -> int:
    """Radiation-hardened voter, implemented in discrete transistor logic (Python)."""
    GateCounter.votes += 1
    return 1 if x + y + z >= 2 else 0


def nand(a: int, b: int) -> int:
    """Triple Modular Redundant NAND: three physical gates and a majority voter."""
    return _majority_voter(_physical_nand(a, b), _physical_nand(a, b), _physical_nand(a, b))


def not_(a: int) -> int:
    return nand(a, a)


def and_(a: int, b: int) -> int:
    return not_(nand(a, b))


def or_(a: int, b: int) -> int:
    return nand(not_(a), not_(b))


def nor(a: int, b: int) -> int:
    return not_(or_(a, b))


def xor(a: int, b: int) -> int:
    t = nand(a, b)
    return nand(nand(a, t), nand(b, t))


def xnor(a: int, b: int) -> int:
    return not_(xor(a, b))


def mux(select: int, a: int, b: int) -> int:
    """Return ``a`` when select is 0, else ``b``."""
    return nand(nand(a, not_(select)), nand(b, select))
