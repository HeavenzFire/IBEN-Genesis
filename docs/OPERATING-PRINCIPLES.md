# HeavenzFire Operating Principles

**Purpose:** build useful, inspectable systems that help people solve problems, protect one another, and create responsibly.

These principles are an engineering contract, not a claim that the project is certified for safety-critical deployment.

## The operating contract

1. **Human safety before task completion.** When safety is uncertain, stop or degrade to a known-safe mode. A successful request is not more important than a safe outcome.
2. **No unbounded authority.** Every model call, tool, agent, and actuator must have explicit scope, resource limits, timeouts, and an authorization boundary. Model output is data, never authorization.
3. **Validate at the receiving boundary.** Do not rely on prompts or provider-side JSON mode. Enforce exact schemas, types, size limits, enumerated actions, and current-state constraints in trusted code.
4. **Fail visibly.** Distinguish success, rejection, timeout, unavailable dependency, budget exhaustion, and recovery failure. Never turn an unknown state into a success-shaped response.
5. **Preserve evidence.** Record versioned inputs, decisions, validation outcomes, errors, timestamps, and integrity hashes where appropriate. Protect logs from secrets and personal data. Hash chaining detects some tampering; it does not by itself prove who created an entry or prevent deletion.
6. **Bound retries and failover.** Use finite budgets, bounded backoff, deadlines, and circuit breakers. A fallback must be explicitly safer than continuing blindly.
7. **Test the failure path.** Inject timeouts, malformed and oversized responses, invalid fields, duplicate messages, stale state, process restarts, storage exhaustion, and network partitions. Test that the safety boundary—not just the happy path—actually runs.
8. **Compare against strong baselines.** Report negative results, uncertainty, latency, resource costs, and test conditions. Do not claim superiority because a demo succeeds.
9. **Make results reproducible.** Version code and test fixtures; document environment, commands, seeds, expected outputs, and limitations. Separate local results, CI results, and independent reproduction.
10. **Least privilege and privacy by default.** Keep credentials out of source control and logs; use scoped credentials, local-first operation where practical, explicit consent, and documented retention.
11. **No unsupported life-saving claims.** A simulation, passing test suite, or successful demo is not evidence of clinical, emergency-response, industrial, or other life-critical readiness. Such use requires domain experts, hazard analysis, independent validation, applicable regulatory review, and deployment-specific monitoring.
12. **Public benefit through accountability.** Welcome criticism and contributions. Explain what is implemented, what is verified, what remains hypothetical, and what failed.

## Model boundary protocol

Treat all model responses as untrusted input, even when they come from a local model.

- Apply a response-size limit before parsing.
- Parse the expected format and reject malformed or ambiguous content.
- Require exact allowed fields; reject unknown fields.
- Enforce strict types (in Python, reject boolean values where an integer is required).
- Check values against current state and an explicit allowlist of legal actions.
- Enforce per-request and per-run call budgets, deadlines, and bounded retries.
- Keep model-generated text separate from executable commands. Never evaluate or execute a model response directly.
- Route rejected, timed-out, or unavailable model calls to a deterministic, reviewed fallback—or stop safely.
- Test adversarial examples such as {"x":3,"y":2,"command":"delete"} against the actual transport and validation path.

## Fault-injection audit checklist

For each fault, capture: injection method, expected invariant, observed result, evidence artifact, recovery result, and any residual risk.

- [ ] Model timeout and repeated timeout
- [ ] Service unavailable or restart during a request
- [ ] Malformed JSON, extra fields, wrong types, and oversized body
- [ ] Authentication failure and provider rate limit
- [ ] Call-budget exhaustion
- [ ] Duplicate, delayed, reordered, and replayed messages
- [ ] Corrupted or partially written state
- [ ] Disk full, memory pressure, and process termination
- [ ] Network partition and recovery
- [ ] Ledger modification, truncation, and restart/resume
- [ ] Fallback failure and safe-stop behavior

A test is a pass only when it asserts the relevant invariant and exercises the real code path. A mocked exception alone is not proof that a production transport path is protected.

## Evidence labels

Use these labels consistently in reports:

- **IMPLEMENTED** — code exists.
- **TESTED** — a named test ran and its result is recorded.
- **CI-VERIFIED** — a named automated workflow passed on a stated revision.
- **REPRODUCED** — another environment or independent operator reproduced the result.
- **BENCHMARKED** — measured against a stated baseline under matched conditions.
- **EXTERNALLY VALIDATED** — reviewed or tested independently by a qualified external party.
- **NOT ESTABLISHED** — evidence is missing, inconclusive, or does not support the claim.

Do not promote a result to a stronger label without new evidence.

## A practical path toward beneficial deployment

1. Reproduce a small, harmless task in a sandbox.
2. Establish deterministic baseline behavior and explicit invariants.
3. Run fault injection and publish the failure table.
4. Review permissions, secrets, privacy, and rollback procedures.
5. Invite external reproduction and adversarial review.
6. For any system that could affect health, physical safety, critical infrastructure, or emergency decisions, require qualified domain review and deployment-specific validation before real-world use.

## Contributing

Submit a minimal reproducible test with each bug report. Include versions, commands, expected versus actual behavior, and sanitized logs. Never include credentials, personal information, or real-world actuation secrets in an issue. Security reports should be shared privately with the maintainers before public disclosure.

**Standard:** no unsupported safety claims, no silent failure, no unbounded authority, and no lost evidence when a component fails.
