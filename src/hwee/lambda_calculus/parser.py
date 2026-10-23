"""Recursive-descent parser for the HWEE Lambda Definition Language (.lc).

Grammar::

    file       := { definition }
    definition := NAME ':=' term
    term       := '\\' NAME { NAME } '.' term | application
    application:= atom { atom }
    atom       := NAME | '(' term ')'
"""

from __future__ import annotations

import re

from hwee.lambda_calculus.terms import NApp, NLam, Named, NVar, Term, to_de_bruijn

_TOKEN = re.compile(r"\s*(?:(#[^\n]*)|(:=)|([\\λ.()])|([@A-Za-z_][A-Za-z0-9_']*))")


def tokenize(source: str) -> list[str]:
    tokens: list[str] = []
    position = 0
    source = source.rstrip()
    while position < len(source):
        match = _TOKEN.match(source, position)
        if not match:
            raise SyntaxError(f"Unexpected character at offset {position}: {source[position]!r}")
        position = match.end()
        if match.group(1):
            continue
        tokens.append(match.group(2) or match.group(3) or match.group(4))
    return tokens


class _Parser:
    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.position = 0

    def peek(self, offset: int = 0) -> str | None:
        index = self.position + offset
        return self.tokens[index] if index < len(self.tokens) else None

    def take(self, expected: str | None = None) -> str:
        token = self.peek()
        if token is None or (expected is not None and token != expected):
            raise SyntaxError(f"Expected {expected!r}, found {token!r}")
        self.position += 1
        return token

    def definitions(self) -> list[tuple[str, Named]]:
        result = []
        while self.peek() is not None:
            name = self.take()
            self.take(":=")
            result.append((name, self.term()))
        return result

    def term(self) -> Named:
        if self.peek() in ("\\", "λ"):
            self.take()
            params = []
            while self.peek() != ".":
                params.append(self.take())
            self.take(".")
            body = self.term()
            for param in reversed(params):
                body = NLam(param, body)
            return body
        return self.application()

    def _starts_atom(self) -> bool:
        token = self.peek()
        if token is None or token in (")", ".", ":=", "\\", "λ"):
            return token in ("\\", "λ")
        return self.peek(1) != ":="

    def application(self) -> Named:
        node = self.atom()
        while self._starts_atom():
            if self.peek() in ("\\", "λ"):
                node = NApp(node, self.term())
                break
            node = NApp(node, self.atom())
        return node

    def atom(self) -> Named:
        token = self.take()
        if token == "(":
            inner = self.term()
            self.take(")")
            return inner
        return NVar(token)


def parse_program(source: str, environment: dict[str, Term] | None = None) -> dict[str, Term]:
    environment = dict(environment or {})
    for name, named in _Parser(tokenize(source)).definitions():
        environment[name] = to_de_bruijn(named, environment)
    return environment
