"""Primes and integer roots, needed to derive SHA-256 constants from first principles."""

from __future__ import annotations


def first_primes(count: int) -> list[int]:
    limit = 16
    while True:
        sieve = bytearray([1]) * (limit + 1)
        sieve[0:2] = b"\x00\x00"
        for p in range(2, int(limit ** 0.5) + 1):
            if sieve[p]:
                sieve[p * p::p] = bytearray(len(sieve[p * p::p]))
        primes = [i for i, flag in enumerate(sieve) if flag]
        if len(primes) >= count:
            return primes[:count]
        limit *= 2


def integer_root(value: int, degree: int) -> int:
    """floor(value ** (1/degree)) by Newton's method on integers."""
    if value < 2:
        return value
    guess = 1 << ((value.bit_length() + degree - 1) // degree)
    while True:
        better = ((degree - 1) * guess + value // guess ** (degree - 1)) // degree
        if better >= guess:
            break
        guess = better
    while guess ** degree > value:
        guess -= 1
    while (guess + 1) ** degree <= value:
        guess += 1
    return guess


def fractional_bits(prime: int, degree: int, bits: int = 32) -> int:
    """First ``bits`` bits of the fractional part of prime ** (1/degree)."""
    return integer_root(prime << (bits * degree), degree) & ((1 << bits) - 1)
