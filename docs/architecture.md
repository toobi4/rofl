# Architecture

```
                 ┌────────────── Composition Root (HelloWorldEnterpriseApplication) ──────────────┐
                 │  Container ── Configuration(HWCONF) ── ResourceLocator(SHA-256 manifest)      │
                 │      │             DeterministicEntropySource(xorshift64*) ── MessageBus      │
                 └──────┼────────────────────────────────────────────────────────────────────────┘
                        ▼
              PipelineOrchestrator (Kahn topological sort over declared artifacts)
                        │
 self-test → provisioning → divination ──► [poly | sha-inversion | bf-on-hwvm | λ | chaos]
                                             │
                                             ▼
                                PBFT cluster (n=5, f=1, view change)
                                             │
                        neural attestation (MLP, autograd, Adam)
                                             │
                     blockchain commit (PoW) → validation → reconstruction
                                             │
                       rasterize → dust → OCR → UTF-8 → Huffman → Base64
                                             │
                        Hamming(7,4) → noisy channel → FEC → CRC-32
                                             │
                    ResilientSink(Retry, CircuitBreaker) → os.write ×14
```

Each stage declares `requires` / `produces`; the orchestrator refuses to run a
stage whose output does not exactly match its contract, and the context refuses
to let an artifact be overwritten.
