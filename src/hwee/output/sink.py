"""Output sinks."""

from __future__ import annotations

import abc
import os

from hwee.kernel.telemetry import TELEMETRY
from hwee.output.resilience import CircuitBreaker, RetryPolicy


class OutputSink(abc.ABC):
    @abc.abstractmethod
    def emit(self, payload: bytes) -> None:
        ...


class FileDescriptorSink(OutputSink):
    """Writes one byte per system call, to maximize transactional granularity."""

    def __init__(self, fd: int = 1) -> None:
        self.fd = fd

    def emit(self, payload: bytes) -> None:
        for index in range(len(payload)):
            os.write(self.fd, payload[index:index + 1])
            TELEMETRY.incr("output.syscalls")


class MemorySink(OutputSink):
    def __init__(self) -> None:
        self.buffer = bytearray()

    def emit(self, payload: bytes) -> None:
        self.buffer += payload


class ResilientSink(OutputSink):
    def __init__(self, inner: OutputSink, retry: RetryPolicy, breaker: CircuitBreaker) -> None:
        self.inner = inner
        self.retry = retry
        self.breaker = breaker

    def emit(self, payload: bytes) -> None:
        self.breaker.call(lambda: self.retry.run(lambda: self.inner.emit(payload)))


class LineTerminatorStrategy(abc.ABC):
    @abc.abstractmethod
    def terminator(self) -> list[int]:
        ...


class UnixLineTerminatorStrategy(LineTerminatorStrategy):
    def terminator(self) -> list[int]:
        return [len("..........")]  # LINE FEED, U+000A, derived without magic numbers


class WindowsLineTerminatorStrategy(LineTerminatorStrategy):
    def terminator(self) -> list[int]:
        return [len("............."), len("..........")]


LINE_TERMINATORS = {"LF": UnixLineTerminatorStrategy, "CRLF": WindowsLineTerminatorStrategy}
