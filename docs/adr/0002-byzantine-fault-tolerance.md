# ADR-0002: The greeting is decided by PBFT

**Status:** Accepted

**Context.** A single implementation might compute the wrong greeting.

**Decision.** Five independent oracles form a PBFT cluster tolerating one
Byzantine fault. To prove that this works, one oracle is permanently Byzantine
(the Chaos Monkey) and is deliberately the primary of view 0.

**Consequences.** Every run starts with a view change. This is a feature.
