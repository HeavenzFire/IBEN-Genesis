"""HeavenzFire Model Gateway — provider-neutral, fail-safe LLM boundary.

Design principles (audit standard: continuity under failure, safe degradation,
recovery, evidence that survives scrutiny):

  1. NO UNBOUNDED AUTHORITY  - every call carries a budget; the gateway tracks
     per-run cost and refuses to exceed it.
  2. STRICT OUTPUT VALIDATION - responses are schema-checked independently of
     the provider. Extra/unknown fields are REJECTED (the pixel-swarm audit
     finding: a legal {x,y} with an injected "command":"delete" must fail).
  3. SAFE DEGRADATION         - providers are tried in order; total failure
     returns a structured FailureResult, never raises into the caller's hot path.
  4. EVIDENCE SURVIVES        - every attempt is appended to a hash-chained
     JSONL ledger so tampering or loss is detectable.
  5. NO SILENT FAILURE        - failures are typed, logged, and hashed.

Providers supported (all via OpenAI-compatible chat/completions API):
  - Ollama local          base_url=http://localhost:11434/v1  model=qwen2.5-coder:7b
  - Qwen Cloud / DashScope base_url=https://dashscope.aliyuncs.com/compatible-mode/v1
  - OpenAI                base_url=https://api.openai.com/v1   model=gpt-4o-mini

Credentials come ONLY from environment variables (never hardcoded):
  OLLAMA_BASE_URL, QWEN_API_KEY / DASHSCOPE_API_KEY, OPENAI_API_KEY
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx


# --------------------------------------------------------------------------
# Results are values, not exceptions — callers can degrade without try/except.
# --------------------------------------------------------------------------

@dataclass
class SuccessResult:
    text: str
    provider: str
    model: str
    latency_ms: float
    attempts: int
    data: Optional[dict] = None          # populated when schema validation ran
    trace_hash: str = ""


@dataclass
class FailureResult:
    reason: str                            # typed, machine-readable
    detail: str = ""
    provider: str = ""
    attempts: int = 0
    degraded_to: Optional[str] = None      # e.g. "bfs_baseline" if caller falls back

    @property
    def ok(self) -> bool:
        return False


# --------------------------------------------------------------------------
# Strict validator — ported from the pixel-swarm audit fix, generalized.
# --------------------------------------------------------------------------

def strict_validate(payload: Any, spec: dict) -> tuple[bool, str]:
    """Validate `payload` against a minimal declarative spec.

    spec example (pixel-swarm action):
        {"type": "object",
         "exact_fields": {"x": "int", "y": "int"},
         "constraint": lambda d: (d["x"], d["y"]) in candidates}

    Rules enforced:
      - object must contain EXACTLY the declared fields (no extras, no missing)
      - ints must be true ints (bools rejected — they subclass int in Python)
      - optional callable constraint runs last
    Returns (ok, reason). Never raises on malformed input.
    """
    if spec.get("type") == "object":
        if not isinstance(payload, dict):
            return False, "not_an_object"
        exact = spec.get("exact_fields", {})
        keys = set(payload.keys())
        if keys != set(exact.keys()):
            extra = sorted(keys - set(exact.keys()))
            missing = sorted(set(exact.keys()) - keys)
            return False, f"field_mismatch extra={extra} missing={missing}"
        for k, want in exact.items():
            v = payload[k]
            if want == "int" and (isinstance(v, bool) or not isinstance(v, int)):
                return False, f"field_{k}_not_int"
            if want == "str" and not isinstance(v, str):
                return False, f"field_{k}_not_str"
        c = spec.get("constraint")
        if c is not None:
            try:
                if not c(payload):
                    return False, "constraint_violated"
            except Exception as e:              # constraint bug => reject, don't crash
                return False, f"constraint_error:{e}"
        return True, "ok"
    return False, "unsupported_spec"


# --------------------------------------------------------------------------
# Hash-chained evidence ledger
# --------------------------------------------------------------------------

class EvidenceLedger:
    def __init__(self, path: str):
        self.path = path
        self._prev = "GENESIS"

    def record(self, event: dict) -> str:
        event = dict(event)
        event["ts"] = time.time()
        event["prev_hash"] = self._prev
        body = json.dumps(event, sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256((self._prev + body).encode()).hexdigest()
        event["hash"] = h
        self._prev = h
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
        return h

    @classmethod
    def verify(cls, path: str) -> tuple[bool, int, str]:
        """Recompute the chain. Returns (valid, records_checked, first_bad_line)."""
        prev = "GENESIS"
        n = 0
        if not os.path.exists(path):
            return True, 0, ""
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                rec = json.loads(line)
                claimed = rec.pop("hash", None)
                if rec.get("prev_hash") != prev:
                    return False, n, f"line {i}: broken prev-link"
                body = json.dumps(rec, sort_keys=True, separators=(",", ":"))
                if hashlib.sha256((prev + body).encode()).hexdigest() != claimed:
                    return False, n, f"line {i}: content mismatch (tampered?)"
                prev = claimed
                n += 1
        return True, n, ""


# --------------------------------------------------------------------------
# Providers (OpenAI-compatible chat endpoint)
# --------------------------------------------------------------------------

MAX_RESPONSE_BYTES = 64 * 1024  # oversized-response rejection, per audit rule


class OpenAICompatProvider:
    def __init__(self, name: str, base_url: str, model: str,
                 api_key: Optional[str] = None, timeout: float = 30.0):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        # Local providers (Ollama) need no key; remote ones do.
        if self.api_key:
            return True
        return "localhost" in self.base_url or "127.0.0.1" in self.base_url

    def complete(self, messages: list[dict], temperature: float = 0.0) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={"model": self.model, "messages": messages,
                  "temperature": temperature},
            timeout=self.timeout,
        )
        # Order matters: reject oversized / non-2xx bodies BEFORE parsing them.
        if len(resp.content) > MAX_RESPONSE_BYTES:
            raise ValueError("oversized_response")
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# --------------------------------------------------------------------------
# Gateway
# --------------------------------------------------------------------------

class ModelGateway:
    """Ordered failover across providers with budget enforcement + evidence."""

    def __init__(self, providers: Optional[list[OpenAICompatProvider]] = None,
                 ledger_path: str = "gateway_evidence.jsonl",
                 max_calls_per_run: int = 50,
                 max_retries: int = 2):
        if providers is None:
            providers = default_providers()
        self.providers = [p for p in providers if p.configured]
        self.unconfigured = [p.name for p in providers if not p.configured]
        self.ledger = EvidenceLedger(ledger_path)
        self.max_calls = max_calls_per_run
        self.max_retries = max_retries
        self.calls_used = 0

    def ask(self, prompt: str, schema: Optional[dict] = None,
            system: str = "You are a precise assistant. Reply with valid JSON only."
            ) -> SuccessResult | FailureResult:
        # Rule: no unbounded authority.
        if self.calls_used >= self.max_calls:
            return FailureResult(reason="budget_exhausted",
                                 detail=f"{self.calls_used}/{self.max_calls} calls used")

        attempts = 0
        last_err = "no_provider_available"
        for prov in self.providers:
            for retry in range(self.max_retries + 1):
                self.calls_used += 1
                attempts += 1
                t0 = time.monotonic()
                try:
                    text = prov.complete(
                        [{"role": "system", "content": system},
                         {"role": "user", "content": prompt}])
                    latency = (time.monotonic() - t0) * 1000
                    data = None
                    if schema is not None:
                        try:
                            parsed = json.loads(_extract_json(text))
                        except json.JSONDecodeError:
                            self._log_fail(prov, "malformed_json", attempts)
                            last_err = "malformed_json"
                            break  # retrying same provider rarely fixes syntax; next provider
                        ok, why = strict_validate(parsed, schema)
                        if not ok:
                            # INDEPENDENT rejection — provider compliance is not trusted.
                            self._log_fail(prov, f"schema_reject:{why}", attempts)
                            last_err = f"schema_reject:{why}"
                            break
                        data = parsed
                    thash = self.ledger.record({
                        "event": "success", "provider": prov.name,
                        "model": prov.model, "latency_ms": round(latency, 2),
                        "attempts": attempts,
                        "resp_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    })
                    return SuccessResult(text=text, provider=prov.name,
                                         model=prov.model, latency_ms=latency,
                                         attempts=attempts, data=data,
                                         trace_hash=thash)
                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    last_err = f"unreachable:{type(e).__name__}"
                    self._log_fail(prov, last_err, attempts)
                    time.sleep(min(2 ** retry * 0.2, 2.0))  # short backoff, bounded
                except httpx.HTTPStatusError as e:
                    code = e.response.status_code
                    if code in (401, 403):
                        last_err = f"auth_failure:{code}"
                        self._log_fail(prov, last_err, attempts)
                        break                      # non-retryable
                    last_err = f"http_{code}"
                    self._log_fail(prov, last_err, attempts)
                except ValueError as e:
                    last_err = str(e)              # e.g. oversized_response
                    self._log_fail(prov, last_err, attempts)
                    break
                except Exception as e:
                    last_err = f"unexpected:{type(e).__name__}"
                    self._log_fail(prov, last_err, attempts)

        # Rule: no silent failure — typed, logged, returned as a value.
        return FailureResult(reason="all_providers_failed", detail=last_err,
                             attempts=attempts,
                             degraded_to="caller_fallback_policy")

    def _log_fail(self, prov, reason, attempts):
        self.ledger.record({"event": "failure", "provider": prov.name,
                            "reason": reason, "attempts": attempts})


def _extract_json(text: str) -> str:
    """Tolerate markdown fences / prose around the JSON object."""
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.startswith("json"):
            s = s[4:]
    start, end = s.find("{"), s.rfind("}")
    if start != -1 and end > start:
        return s[start:end + 1]
    return s


def default_providers() -> list[OpenAICompatProvider]:
    """Order: local-first (private, free), then Qwen cloud, then OpenAI."""
    return [
        OpenAICompatProvider(
            "ollama-local",
            os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")),
        OpenAICompatProvider(
            "qwen-cloud",
            os.environ.get("QWEN_BASE_URL",
                           "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            os.environ.get("QWEN_MODEL", "qwen-coder-plus"),
            api_key=os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY")),
        OpenAICompatProvider(
            "openai",
            os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            os.environ.get("GPT_MODEL", "gpt-4o-mini"),
            api_key=os.environ.get("OPENAI_API_KEY")),
    ]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="HeavenzFire model gateway")
    ap.add_argument("prompt", nargs="?", help="prompt to send")
    ap.add_argument("--status", action="store_true", help="show provider config state")
    ap.add_argument("--verify-ledger", action="store_true")
    args = ap.parse_args()

    if args.verify_ledger:
        ok, n, bad = EvidenceLedger.verify("gateway_evidence.jsonl")
        print(f"ledger valid={ok} records={n} first_bad={bad!r}")
    elif args.status or not args.prompt:
        gw = ModelGateway()
        print("Configured providers (failover order):",
              [f"{p.name}:{p.model}" for p in gw.providers] or "NONE")
        print("Unconfigured (need API key / service):", gw.unconfigured or "none")
        print(f"Budget: {gw.max_calls} calls/run")
    else:
        r = ModelGateway().ask(args.prompt)
        print(json.dumps(r.__dict__, indent=2, default=str))
