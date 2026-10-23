"""Resilience patterns for the extremely unreliable act of writing to stdout."""

from __future__ import annotations

import enum
import time
from typing import Callable, TypeVar

from hwee.kernel.errors import CircuitOpenError
from hwee.kernel.telemetry import TELEMETRY

T = TypeVar("T")


class RetryPolicy:
    def __init__(self, attempts: int = 5, base_delay: float = 0.001, factor: float = 2.0) -> None:
        self.attempts = attempts
        self.base_delay = base_delay
        self.factor = factor

    def run(self, operation: Callable[[], T]) -> T:
        delay = self.base_delay
        for attempt in range(1, self.attempts + 1):
            try:
                return operation()
            except OSError:
                TELEMETRY.incr("output.retries")
                if attempt == self.attempts:
                    raise
                time.sleep(delay)
                delay *= self.factor
        raise AssertionError("unreachable")


class BreakerState(enum.Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 1.0) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = BreakerState.CLOSED
        self.failures = 0
        self.opened_at = 0.0

    def call(self, operation: Callable[[], T]) -> T:
        if self.state is BreakerState.OPEN:
            if time.monotonic() - self.opened_at < self.reset_timeout:
                raise CircuitOpenError("Output circuit is open; refusing to greet")
            self.state = BreakerState.HALF_OPEN
        try:
            result = operation()
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold or self.state is BreakerState.HALF_OPEN:
                self.state = BreakerState.OPEN
                self.opened_at = time.monotonic()
            raise
        self.failures = 0
        self.state = BreakerState.CLOSED
        return result
