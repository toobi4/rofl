# ADR-0005: One system call per byte

**Status:** Accepted

**Context.** Buffered writes could partially fail, leaving the greeting
half-delivered and the user half-greeted.

**Decision.** Each byte is written with its own `os.write`, wrapped in a retry
policy with exponential backoff, wrapped in a circuit breaker.

**Consequences.** The greeting is delivered with 14-fold transactional granularity.
