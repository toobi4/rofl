"""Typed, path-addressable configuration model."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

from hwee.config.parser import ConfigParser
from hwee.kernel.errors import ConfigurationError

T = TypeVar("T")
_MISSING = object()


class Configuration:
    def __init__(self, tree: dict) -> None:
        self._tree = tree

    @classmethod
    def from_file(cls, path: str | Path) -> "Configuration":
        return cls(ConfigParser(Path(path).read_text(encoding="utf-8")).parse())

    @classmethod
    def from_string(cls, source: str) -> "Configuration":
        return cls(ConfigParser(source).parse())

    def get(self, path: str, expected: type[T] = object, default: Any = _MISSING) -> T:
        node: Any = self._tree
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                if default is _MISSING:
                    raise ConfigurationError(f"Missing configuration key {path!r}")
                return default
            node = node[part]
        if expected is float and isinstance(node, int):
            node = float(node)
        if not isinstance(node, expected):
            raise ConfigurationError(f"{path!r}: expected {expected.__name__}, got {type(node).__name__}")
        return node

    def override(self, path: str, value: Any) -> None:
        *parents, leaf = path.split(".")
        node = self._tree
        for part in parents:
            node = node.setdefault(part, {})
        node[leaf] = value

    def section(self, path: str) -> "Configuration":
        return Configuration(self.get(path, dict))
