#!/usr/bin/env python3
"""Artifact Forge: compiles a greeting into the encoded artifacts consumed by the oracles.

This is a build-time tool. The runtime never sees the greeting in plain text.

    python tools/forge_artifacts.py --greeting "<text>" [--out src/hwee/resources]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import secrets
from fractions import Fraction
from pathlib import Path

NUMERALS = ["ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN",
            "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN"]


def lagrange(values: list[int]) -> tuple[list[int], int]:
    n = len(values)
    coefficients = [Fraction(0)] * n
    for i, yi in enumerate(values):
        basis = [Fraction(1)]
        denominator = Fraction(1)
        for j in range(n):
            if j == i:
                continue
            basis = [Fraction(0)] + basis
            for k in range(len(basis) - 1):
                basis[k] -= j * basis[k + 1]
            denominator *= i - j
        for k in range(n):
            coefficients[k] += yi * basis[k] / denominator
    common = 1
    for c in coefficients:
        common = common * c.denominator // math.gcd(common, c.denominator)
    numerators = [int(c * common) for c in coefficients]
    for x, y in enumerate(values):
        assert sum(c * x ** k for k, c in enumerate(numerators)) == y * common
    return numerators, common


def church(n: int) -> str:
    if n <= 16:
        return NUMERALS[n]
    quotient, remainder = divmod(n, 16)
    return f"ADD (MUL SIXTEEN ({church(quotient)})) {NUMERALS[remainder]}"


def brainfuck(values: list[int]) -> str:
    out, current = [], 0
    for value in values:
        delta = value - current
        sign = "+" if delta > 0 else "-"
        magnitude = abs(delta)
        if magnitude >= 12:
            a = math.isqrt(magnitude)
            b, r = divmod(magnitude, a)
            out.append(">" + "+" * a + "[<" + sign * b + ">-]<" + sign * r)
        else:
            out.append(sign * magnitude)
        out.append(".")
        current = value
    body = "".join(out)
    lines = [body[i:i + 64] for i in range(0, len(body), 64)]
    return "HWEE Greeting Program (generated; do not edit)\n" + "\n".join(lines) + "\n"


def lcg_space(modulus: int) -> dict:
    return {"modulus": modulus, "multiplier": 4 * secrets.randbelow(modulus // 4) + 1,
            "increment": 2 * secrets.randbelow(modulus // 2) + 1, "seed": secrets.randbelow(modulus)}


def stretched(data: bytes, iterations: int) -> bytes:
    for _ in range(iterations):
        data = hashlib.sha256(data).digest()
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--greeting", required=True)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "src/hwee/resources"))
    parser.add_argument("--iterations", type=int, default=2)
    parser.add_argument("--search-space", type=int, default=4096)
    args = parser.parse_args()
    out = Path(args.out)
    values = [ord(ch) for ch in args.greeting]
    if max(values) >= args.search_space:
        raise SystemExit("search space too small for this greeting")

    numerators, denominator = lagrange(values)
    (out / "greeting.poly.json").write_text(json.dumps({
        "schema": "hwee/polynomial@1", "points": len(values), "denominator": str(denominator),
        "coefficients": [str(c) for c in numerators]}, indent=2) + "\n")

    salt = secrets.token_bytes(16)
    digests = [stretched(salt + i.to_bytes(4, "big") + v.to_bytes(4, "big"), args.iterations).hex()
               for i, v in enumerate(values)]
    (out / "greeting.digests.json").write_text(json.dumps({
        "schema": "hwee/preimage@1", "salt": salt.hex(), "iterations": args.iterations,
        "search_space": lcg_space(args.search_space), "digests": digests}, indent=2) + "\n")

    (out / "greeting.bf").write_text(brainfuck(values))

    lines = ["# HWEE Greeting in Church encoding (generated; do not edit)"]
    lines += [f"@{i} := ADD ({church(v)}) ZERO" for i, v in enumerate(values)]
    (out / "greeting.lc").write_text("\n".join(lines) + "\n")

    artifacts = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.suffix not in (".py", ".pyc") and path.name != "MANIFEST.json":
            artifacts[path.relative_to(out).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    (out / "MANIFEST.json").write_text(json.dumps({"schema": "hwee/manifest@1", "artifacts": artifacts},
                                                  indent=2) + "\n")
    print(f"Forged {len(artifacts)} artifacts into {out}")


if __name__ == "__main__":
    main()
