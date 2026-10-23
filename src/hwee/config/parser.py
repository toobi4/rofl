"""Recursive-descent parser for HWCONF with environment interpolation.

Interpolation syntax: ``${env:NAME:-default}``.
"""

from __future__ import annotations

import ast
import os

from hwee.config.lexer import Kind, Token, tokenize
from hwee.kernel.errors import ConfigurationError

_TRUE = {"true", "yes", "on", "enterprise_true"}


class ConfigParser:
    def __init__(self, source: str, environ: dict[str, str] | None = None) -> None:
        self.tokens = tokenize(source)
        self.position = 0
        self.environ = os.environ if environ is None else environ

    def _peek(self) -> Token:
        return self.tokens[self.position]

    def _take(self, kind: Kind) -> Token:
        token = self._peek()
        if token.kind is not kind:
            raise ConfigurationError(f"line {token.line}: expected {kind.value}, found {token.text!r}")
        self.position += 1
        return token

    def parse(self) -> dict:
        root: dict = {}
        section = root
        while self._peek().kind is not Kind.EOF:
            token = self._peek()
            if token.kind is Kind.NEWLINE:
                self.position += 1
            elif token.kind is Kind.LBRACKET:
                self.position += 1
                path = self._take(Kind.KEY).text
                self._take(Kind.RBRACKET)
                section = self._descend(root, path.split("."))
            elif token.kind is Kind.KEY:
                key = self._take(Kind.KEY).text
                self._take(Kind.EQUALS)
                *parents, leaf = key.split(".")
                target = self._descend(section, parents)
                target[leaf] = self._value()
            else:
                raise ConfigurationError(f"line {token.line}: unexpected {token.text!r}")
        return root

    @staticmethod
    def _descend(node: dict, path: list[str]) -> dict:
        for part in path:
            node = node.setdefault(part, {})
            if not isinstance(node, dict):
                raise ConfigurationError(f"{part!r} is both a value and a section")
        return node

    def _value(self):
        token = self._peek()
        self.position += 1
        if token.kind is Kind.STRING:
            return ast.literal_eval(token.text)
        if token.kind is Kind.INTEGER:
            return int(token.text.replace("_", ""), 0)
        if token.kind is Kind.FLOAT:
            return float(token.text)
        if token.kind is Kind.BOOLEAN:
            return token.text in _TRUE
        if token.kind is Kind.INTERPOLATION:
            return self._interpolate(token)
        raise ConfigurationError(f"line {token.line}: expected a value, found {token.text!r}")

    def _interpolate(self, token: Token):
        expression = token.text[2:-1]
        provider, _, rest = expression.partition(":")
        if provider != "env":
            raise ConfigurationError(f"line {token.line}: unknown interpolation provider {provider!r}")
        name, _, default = rest.partition(":-")
        raw = self.environ.get(name, default)
        nested = ConfigParser(f"value = {raw}\n" if raw else 'value = ""\n', self.environ)
        try:
            return nested.parse()["value"]
        except ConfigurationError:
            return raw
