"""Natural numbers as little-endian bit vectors, computed exclusively via circuits."""

from __future__ import annotations

from hwee.logic.circuits import equality_comparator, ripple_carry_adder, subtractor


def _normalize(bits: list[int]) -> tuple[int, ...]:
    end = len(bits)
    while end and bits[end - 1] == 0:
        end -= 1
    return tuple(bits[:end])


class BigNat:
    __slots__ = ("bits",)

    def __init__(self, bits: list[int] | tuple[int, ...] = ()) -> None:
        self.bits = _normalize(list(bits))

    # --- construction -----------------------------------------------------
    @classmethod
    def zero(cls) -> "BigNat":
        return cls(())

    @classmethod
    def one(cls) -> "BigNat":
        return cls((1,))

    @classmethod
    def from_decimal(cls, text: str) -> "BigNat":
        """Parse a decimal string by Horner's rule on gate-level arithmetic."""
        digits = _digit_table()
        ten = digits["9"] + cls.one()
        value = cls.zero()
        for char in text.strip():
            if char == "_":
                continue
            if char not in digits:
                raise ValueError(f"Invalid decimal digit {char!r}")
            value = value * ten + digits[char]
        return value

    def to_python_int(self) -> int:
        """Anti-corruption layer towards the legacy integer subsystem."""
        result = 0
        for index, bit in enumerate(self.bits):
            if bit:
                result |= 1 << index
        return result

    # --- predicates ---------------------------------------------------------
    def is_zero(self) -> bool:
        return not self.bits

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BigNat):
            return NotImplemented
        return bool(equality_comparator(list(self.bits), list(other.bits)))

    def __hash__(self) -> int:
        return hash(self.bits)

    def __ge__(self, other: "BigNat") -> bool:
        _, no_borrow = subtractor(list(self.bits), list(other.bits))
        return bool(no_borrow)

    def __lt__(self, other: "BigNat") -> bool:
        return not self >= other

    # --- arithmetic ---------------------------------------------------------
    def __add__(self, other: "BigNat") -> "BigNat":
        total, carry = ripple_carry_adder(list(self.bits), list(other.bits))
        return BigNat(total + [carry])

    def __sub__(self, other: "BigNat") -> "BigNat":
        difference, no_borrow = subtractor(list(self.bits), list(other.bits))
        if not no_borrow:
            raise ArithmeticError("Natural subtraction underflow")
        return BigNat(difference)

    def shifted(self, amount: int) -> "BigNat":
        return BigNat([0] * amount + list(self.bits)) if self.bits else self

    def __mul__(self, other: "BigNat") -> "BigNat":
        product = BigNat.zero()
        for index, bit in enumerate(other.bits):
            if bit:
                product = product + self.shifted(index)
        return product

    def __divmod__(self, divisor: "BigNat") -> tuple["BigNat", "BigNat"]:
        if divisor.is_zero():
            raise ZeroDivisionError("BigNat division by zero")
        quotient = [0] * len(self.bits)
        remainder = BigNat.zero()
        for index in range(len(self.bits) - 1, -1, -1):
            remainder = BigNat((self.bits[index],) + remainder.bits)
            if remainder >= divisor:
                remainder = remainder - divisor
                quotient[index] = 1
        return BigNat(quotient), remainder

    def __repr__(self) -> str:
        return f"BigNat(0b{''.join(map(str, reversed(self.bits))) or '0'})"


_DIGITS: dict[str, BigNat] | None = None


def _digit_table() -> dict[str, BigNat]:
    """Digits are defined by repeated succession from zero, as Peano intended."""
    global _DIGITS
    if _DIGITS is None:
        table: dict[str, BigNat] = {}
        current = BigNat.zero()
        for symbol in "0123456789":
            table[symbol] = current
            current = current + BigNat.one()
        _DIGITS = table
    return _DIGITS
