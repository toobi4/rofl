"""Tokenizer for HWCONF."""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass

from hwee.kernel.errors import ConfigurationError


class Kind(enum.Enum):
    LBRACKET = "["
    RBRACKET = "]"
    EQUALS = "="
    KEY = "key"
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    INTERPOLATION = "interpolation"
    NEWLINE = "newline"
    EOF = "eof"


@dataclass(frozen=True)
class Token:
    kind: Kind
    text: str
    line: int


_RULES = [
    (Kind.NEWLINE, r"\n"),
    (None, r"[ \t\r]+|#[^\n]*"),
    (Kind.LBRACKET, r"\["),
    (Kind.RBRACKET, r"\]"),
    (Kind.EQUALS, r"="),
    (Kind.INTERPOLATION, r"\$\{[^}]*\}"),
    (Kind.STRING, r'"(?:[^"\\]|\\.)*"'),
    (Kind.FLOAT, r"[+-]?\d+\.\d+(?:[eE][+-]?\d+)?"),
    (Kind.INTEGER, r"[+-]?(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|\d[\d_]*)"),
    (Kind.BOOLEAN, r"\b(?:true|false|yes|no|on|off|enterprise_true)\b"),
    (Kind.KEY, r"[A-Za-z_][A-Za-z0-9_.\-]*"),
]
_MASTER = re.compile("|".join(f"(?P<g{i}>{pattern})" for i, (_, pattern) in enumerate(_RULES)))


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    line = 1
    position = 0
    while position < len(source):
        match = _MASTER.match(source, position)
        if match is None:
            raise ConfigurationError(f"line {line}: unexpected character {source[position]!r}")
        index = int(match.lastgroup[1:])
        kind = _RULES[index][0]
        text = match.group()
        if kind is not None:
            tokens.append(Token(kind, text, line))
        if kind is Kind.NEWLINE:
            line += 1
        position = match.end()
    tokens.append(Token(Kind.EOF, "", line))
    return tokens
