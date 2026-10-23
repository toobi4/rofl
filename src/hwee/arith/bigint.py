"""Signed integers in sign-magnitude representation over BigNat."""

from __future__ import annotations

from hwee.arith.bignat import BigNat


class BigInt:
    __slots__ = ("negative", "magnitude")

    def __init__(self, magnitude: BigNat, negative: bool = False) -> None:
        self.magnitude = magnitude
        self.negative = negative and not magnitude.is_zero()

    @classmethod
    def from_decimal(cls, text: str) -> "BigInt":
        text = text.strip()
        negative = text.startswith("-")
        return cls(BigNat.from_decimal(text.lstrip("+-")), negative)

    def to_python_int(self) -> int:
        value = self.magnitude.to_python_int()
        return -value if self.negative else value

    def __neg__(self) -> "BigInt":
        return BigInt(self.magnitude, not self.negative)

    def __add__(self, other: "BigInt") -> "BigInt":
        if self.negative == other.negative:
            return BigInt(self.magnitude + other.magnitude, self.negative)
        if self.magnitude >= other.magnitude:
            return BigInt(self.magnitude - other.magnitude, self.negative)
        return BigInt(other.magnitude - self.magnitude, other.negative)

    def __sub__(self, other: "BigInt") -> "BigInt":
        return self + (-other)

    def __mul__(self, other: "BigInt") -> "BigInt":
        return BigInt(self.magnitude * other.magnitude, self.negative != other.negative)

    def exact_div(self, other: "BigInt") -> "BigInt":
        quotient, remainder = divmod(self.magnitude, other.magnitude)
        if not remainder.is_zero():
            raise ArithmeticError("Inexact division in exact_div")
        return BigInt(quotient, self.negative != other.negative)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BigInt):
            return NotImplemented
        return self.negative == other.negative and self.magnitude == other.magnitude

    def __hash__(self) -> int:
        return hash((self.negative, self.magnitude.bits))

    def __repr__(self) -> str:
        return f"BigInt({'-' if self.negative else ''}{self.magnitude!r})"
