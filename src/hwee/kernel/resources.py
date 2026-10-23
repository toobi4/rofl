"""Resource locator with manifest-based SHA-256 integrity verification."""

from __future__ import annotations

import json
from importlib import resources

from hwee.crypto.sha256 import sha256_hex
from hwee.kernel.errors import IntegrityError
from hwee.kernel.telemetry import TELEMETRY

MANIFEST = "MANIFEST.json"


class ResourceLocator:
    def __init__(self, package: str = "hwee.resources") -> None:
        self._root = resources.files(package)
        self._manifest: dict[str, str] | None = None
        self._cache: dict[str, bytes] = {}

    def manifest(self) -> dict[str, str]:
        if self._manifest is None:
            self._manifest = json.loads(self._root.joinpath(MANIFEST).read_text(encoding="utf-8"))["artifacts"]
        return self._manifest

    def read_bytes(self, name: str) -> bytes:
        if name in self._cache:
            return self._cache[name]
        expected = self.manifest().get(name)
        if expected is None:
            raise IntegrityError(f"Artifact {name!r} is not listed in the manifest")
        blob = self._root.joinpath(*name.split("/")).read_bytes()
        actual = sha256_hex(blob)
        if actual != expected:
            raise IntegrityError(f"Artifact {name!r} failed integrity check: {actual} != {expected}")
        TELEMETRY.incr("resources.verified")
        self._cache[name] = blob
        return blob

    def read_text(self, name: str) -> str:
        return self.read_bytes(name).decode("utf-8")

    def read_json(self, name: str) -> dict:
        return json.loads(self.read_text(name))
