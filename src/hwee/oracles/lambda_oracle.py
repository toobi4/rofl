"""Church Encoding Oracle: code points as normal forms of lambda terms."""

from __future__ import annotations

import sys

from hwee.kernel.plugins import plugin
from hwee.lambda_calculus.church import decode_numeral
from hwee.lambda_calculus.parser import parse_program
from hwee.lambda_calculus.reducer import normalize
from hwee.oracles.base import GlyphOracle


@plugin("oracle", "lambda", priority=50)
class ChurchEncodingOracle(GlyphOracle):
    PRELUDE = "prelude.lc"
    PROGRAM = "greeting.lc"

    def divine(self) -> list[int]:
        sys.setrecursionlimit(max(sys.getrecursionlimit(), 50_000))
        environment = parse_program(self.resources.read_text(self.PRELUDE))
        environment = parse_program(self.resources.read_text(self.PROGRAM), environment)
        slots = sorted((int(name[1:]), term) for name, term in environment.items() if name.startswith("@"))
        limit = self.setting("reduction_limit", int, 1_000_000)
        return [decode_numeral(normalize(term, limit)[0]) for _, term in slots]
