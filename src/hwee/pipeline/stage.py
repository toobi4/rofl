"""Stage abstraction and the pipeline context."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any

from hwee.kernel.errors import HweeError


@dataclass
class PipelineContext:
    artifacts: dict[str, Any] = field(default_factory=dict)
    audit_log: list[str] = field(default_factory=list)

    def put(self, key: str, value: Any, producer: str) -> None:
        if key in self.artifacts:
            raise HweeError(f"Artifact {key!r} is immutable once produced")
        self.artifacts[key] = value
        self.audit_log.append(f"{producer} produced {key}")

    def require(self, key: str) -> Any:
        if key not in self.artifacts:
            raise HweeError(f"Required artifact {key!r} has not been produced yet")
        return self.artifacts[key]


class Stage(abc.ABC):
    name = "unnamed-stage"
    requires: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()

    @abc.abstractmethod
    def execute(self, context: PipelineContext) -> dict[str, Any]:
        """Return the artifacts produced by this stage."""
