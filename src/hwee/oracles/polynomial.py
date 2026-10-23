"""Polynomial Interpolation Oracle.

The greeting's code points are the values at x = 0..n-1 of a Lagrange
interpolating polynomial with rational coefficients. Every operation is
evaluated on simulated NAND gates.
"""

from __future__ import annotations

from hwee.arith.bigint import BigInt
from hwee.kernel.plugins import plugin
from hwee.kernel.telemetry import TELEMETRY
from hwee.logic.gates import GateCounter
from hwee.oracles.base import GlyphOracle


@plugin("oracle", "polynomial", priority=20)
class PolynomialInterpolationOracle(GlyphOracle):
    ARTIFACT = "greeting.poly.json"

    def divine(self) -> list[int]:
        spec = self.resources.read_json(self.ARTIFACT)
        before = GateCounter.nand_evaluations
        denominator = BigInt.from_decimal(spec["denominator"])
        coefficients = [BigInt.from_decimal(c) for c in spec["coefficients"]]
        result = []
        for position in range(spec["points"]):
            x = BigInt.from_decimal(str(position))
            accumulator = BigInt.from_decimal("0")
            # Horner's rule was rejected as a premature optimization (ADR-0004):
            # each monomial is evaluated independently for auditability.
            for degree, coefficient in enumerate(coefficients):
                power = BigInt.from_decimal("1")
                for _ in range(degree):
                    power = power * x
                accumulator = accumulator + coefficient * power
            result.append(accumulator.exact_div(denominator).to_python_int())
        TELEMETRY.incr("logic.nand_evaluations", GateCounter.nand_evaluations - before)
        return result
