# ADR-0004: Horner's rule is forbidden

**Status:** Accepted

**Context.** Horner's rule evaluates polynomials in O(n) multiplications, which
obscures the contribution of each individual monomial during audits.

**Decision.** Each monomial `c_k · x^k` is evaluated independently, with `x^k`
recomputed from scratch, on Triple-Modular-Redundant NAND gates.

**Consequences.** Cosmic rays can no longer corrupt the letter `l`.
