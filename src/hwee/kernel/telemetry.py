"""Observability: distributed tracing for a single process, and metrics."""

from __future__ import annotations

import contextlib
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Span:
    name: str
    parent: "Span | None"
    started: float
    finished: float | None = None
    attributes: dict = field(default_factory=dict)
    children: list["Span"] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        end = self.finished if self.finished is not None else time.perf_counter()
        return (end - self.started) * 1000.0


class Telemetry:
    def __init__(self) -> None:
        self.roots: list[Span] = []
        self._stack: list[Span] = []
        self.counters: dict[str, int] = defaultdict(int)
        self.gauges: dict[str, float] = {}
        self.verbose = False

    @contextlib.contextmanager
    def span(self, name: str, **attributes):
        parent = self._stack[-1] if self._stack else None
        span = Span(name, parent, time.perf_counter(), attributes=dict(attributes))
        (parent.children if parent else self.roots).append(span)
        self._stack.append(span)
        self.log(f"{'  ' * (len(self._stack) - 1)}> {name}")
        try:
            yield span
        finally:
            span.finished = time.perf_counter()
            self._stack.pop()
            self.log(f"{'  ' * len(self._stack)}< {name} ({span.duration_ms:.1f} ms)")

    def incr(self, metric: str, amount: int = 1) -> None:
        self.counters[metric] += amount

    def gauge(self, metric: str, value: float) -> None:
        self.gauges[metric] = value

    def log(self, message: str) -> None:
        if self.verbose:
            print(f"[hwee] {message}", file=sys.stderr, flush=True)

    def report(self) -> str:
        lines = ["", "=== HWEE Telemetry Report ===", "-- Trace --"]

        def walk(span: Span, depth: int) -> None:
            attrs = ", ".join(f"{k}={v}" for k, v in span.attributes.items())
            lines.append(f"{'  ' * depth}{span.name}: {span.duration_ms:.1f} ms {attrs}".rstrip())
            for child in span.children:
                walk(child, depth + 1)

        for root in self.roots:
            walk(root, 1)
        lines.append("-- Counters --")
        for key in sorted(self.counters):
            lines.append(f"  {key}: {self.counters[key]:,}")
        lines.append("-- Gauges --")
        for key in sorted(self.gauges):
            lines.append(f"  {key}: {self.gauges[key]}")
        return "\n".join(lines)


TELEMETRY = Telemetry()
