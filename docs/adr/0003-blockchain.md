# ADR-0003: The greeting is recorded on a blockchain

**Status:** Accepted

**Context.** Auditors asked how we know the greeting was not tampered with
between consensus and output.

**Decision.** Each code point is committed to a proof-of-work block, the chain is
validated in full, and the greeting is reconstructed from the ledger.

**Consequences.** Latency is now tunable via `HWEE_DIFFICULTY`. Sales calls this
"elastic performance".
