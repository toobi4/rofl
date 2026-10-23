# ADR-0001: Zero third-party dependencies

**Status:** Accepted

**Context.** Supply-chain attacks are a risk. The greeting is critical.

**Decision.** We implement everything ourselves: SHA-256, CRC-32, UTF-8, Base64,
Huffman, Hamming codes, arbitrary-precision arithmetic, automatic differentiation,
a configuration language, a JSON-schema validator, a virtual machine and a lambda
calculus reducer.

**Consequences.** We now have a supply chain of one. Its name is `hwee`.
