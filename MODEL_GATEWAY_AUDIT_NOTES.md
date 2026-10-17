# Model Gateway — Audit Notes (Phase: fault injection at the model boundary)

Date: 2026-10-17
Scope: /workspace/model_gateway.py, /workspace/test_model_gateway.py
Standard applied: continuity under failure, safe degradation, recovery,
evidence that survives independent scrutiny. No unsupported safety claims.

## What was built
A provider-neutral LLM boundary for Qwen Coder / HeavenzFire swarm use:
- Failover order: ollama-local (qwen2.5-coder:7b) → qwen-cloud (DashScope,
  OpenAI-compatible) → openai. Selected by env config, never hardcoded keys.
- Results are values (SuccessResult / FailureResult), not exceptions —
  callers degrade without try/except in hot paths.
- strict_validate(): generalized port of the pixel-swarm audit fix.
  Rejects extra fields, missing fields, bool-as-int, constraint violations,
  and oversized bodies (>64 KiB) INDEPENDENTLY of provider compliance.
- EvidenceLedger: hash-chained JSONL; every success AND failure is hashed.
  verify() recomputes the chain and localizes tampering to a line number.
- Budget enforcement: max_calls_per_run hard stop (no unbounded authority).

## Faults injected and outcomes (all via regression tests, no network)
| Fault                          | Detected | Safe state | Evidence kept | Recovered |
|--------------------------------|----------|------------|---------------|-----------|
| Provider timeout               | yes      | failover   | ledger entry  | next provider |
| Service unreachable (refused)  | yes      | typed fail | ledger entry  | caller fallback advertised |
| Malformed JSON reply           | yes      | reject     | ledger entry  | next provider |
| Smuggled field {x,y,command}   | yes      | reject     | ledger entry  | n/a (rejected) |
| Oversized response             | yes      | reject     | ledger entry  | n/a |
| Auth failure (401)             | yes      | non-retry  | ledger entry  | next provider |
| Ledger tampering               | yes      | verify fails w/ line no. | — | — |
| Budget exhaustion              | yes      | hard stop  | — | caller degrades |

## Test-gate finding (honest note)
The first oversized-response test FAILED against the real code: the gateway
had been trusting FakeProvider's scripted exception instead of exercising the
transport check, and the original size-check ordering could parse hostile
bodies before rejecting them. Fixed: size check now runs BEFORE raise_for_status
/ json parsing; the test now injects the fault at the httpx layer through the
real OpenAICompatProvider.complete(). This is exactly the kind of gap the
audit standard is meant to catch — a protection that exists but is not on the
tested path.

## Verified status
- 19/19 gateway fault-injection tests pass (unittest + pytest)
- 103/103 combined suite passes (gateway + pre-existing engines; legacy suites
  needed pytest<8 due to a mark-on-fixture deprecation unrelated to this work)
- Ledger verify: valid=True on clean chain, localizes edited records
- Environment scan: NO API keys present in this sandbox; Ollama not running
  here (checked localhost:11434 — refused). Live calls therefore remain
  UNTESTED from this environment. Evidence: gateway --status shows only
  ollama-local as configured-by-default; qwen-cloud/openai need keys.

## Distinctions kept explicit
- Passing these tests is evidence about the tested conditions only.
- Nothing here certifies life-critical readiness or changes actuation.
- The model-assisted policy's advantage over BFS remains undemonstrated;
  the gateway does not claim otherwise.

## Next phase candidates
1. Live smoke test once a key/Ollama endpoint is reachable (desktop side).
2. Duplicate-message & network-partition faults at the swarm level (gateway
   already dedups via trace_hash; needs cross-agent clock-ordering design).
3. Corrupted-state recovery: restart gateway mid-run, resume ledger chain
   from last verified hash instead of GENESIS.
4. Wire pixel-swarm's Ollama policy call through ModelGateway so simulator
   runs inherit budget + validation + evidence automatically.
