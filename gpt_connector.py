#!/usr/bin/env python3
"""
================================================================================
GPT CONNECTOR - OpenAI API Bridge for the Sovereign Pipeline
================================================================================

Provides a thin, resilient client for connecting the project's engines to
OpenAI's GPT models (Chat Completions API).

Design goals:
  - Reads credentials from environment (OPENAI_API_KEY) or .env file.
    Never hardcodes secrets.
  - Retries with exponential backoff on transient failures.
  - Structured JSON output helper for pipeline integration.
  - Graceful degradation: clear errors when no key / network is available.

Usage:
  from gpt_connector import GPTConnector

  gpt = GPTConnector()                      # default model: gpt-4o-mini
  reply = gpt.chat("Summarize this ledger") # plain text reply
  data  = gpt.chat_json("List overdue FOIA requests as JSON")  # parsed dict

CLI:
  python gpt_connector.py --test            # connectivity smoke test
  python gpt_connector.py "your prompt"     # one-shot chat
================================================================================
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

DEFAULT_MODEL = os.environ.get("GPT_MODEL", "gpt-4o-mini")
DEFAULT_BASE_URL = os.environ.get("OPENAI_BASE_URL", None)  # allow proxies
MAX_RETRIES = int(os.environ.get("GPT_MAX_RETRIES", "3"))
RETRY_BACKOFF = float(os.environ.get("GPT_RETRY_BACKOFF", "2.0"))
REQUEST_TIMEOUT = float(os.environ.get("GPT_TIMEOUT", "60"))


class GPTConnectorError(RuntimeError):
    """Raised when the connector cannot fulfil a request."""


def _load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader (KEY=VALUE lines) so we don't need python-dotenv."""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("'\"")
            os.environ.setdefault(key, value)


class GPTConnector:
    """Resilient wrapper around the OpenAI Chat Completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        base_url: Optional[str] = DEFAULT_BASE_URL,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ):
        if OpenAI is None:
            raise GPTConnectorError(
                "The 'openai' package is not installed. Run: pip install openai"
            )

        _load_dotenv()
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise GPTConnectorError(
                "OPENAI_API_KEY not found. Set it in your environment:\n"
                "  export OPENAI_API_KEY='sk-...'\n"
                "or add it to a .env file next to this script."
            )

        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt or (
            "You are a precise engineering assistant integrated into an "
            "automated accountability pipeline. Answer concisely and "
            "accurately."
        )
        self._client = OpenAI(api_key=api_key, base_url=base_url,
                              timeout=REQUEST_TIMEOUT)

    # ------------------------------------------------------------------ #
    # Core call with retry/backoff
    # ------------------------------------------------------------------ #
    def _create(self, messages: List[Dict[str, str]],
                response_format: Optional[Dict[str, str]] = None) -> str:
        last_err: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                kwargs: Dict[str, Any] = dict(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                )
                if response_format is not None:
                    kwargs["response_format"] = response_format
                resp = self._client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except Exception as exc:  # noqa: BLE001 - classify below
                name = type(exc).__name__
                # Non-retryable auth/permission errors
                if "AuthenticationError" in name or "PermissionDeniedError" in name:
                    raise GPTConnectorError(f"GPT auth failure: {exc}") from exc
                last_err = exc
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF ** attempt
                    print(f"[gpt_connector] attempt {attempt} failed "
                          f"({name}); retrying in {wait:.1f}s", file=sys.stderr)
                    time.sleep(wait)
        raise GPTConnectorError(
            f"GPT request failed after {MAX_RETRIES} attempts: {last_err}"
        )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def chat(self, prompt: str, history: Optional[List[Dict[str, str]]] = None,
             temperature: Optional[float] = None) -> str:
        """Single-turn (or continued) chat; returns plain text."""
        saved = self.temperature
        if temperature is not None:
            self.temperature = temperature
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": prompt})
            return self._create(messages)
        finally:
            self.temperature = saved

    def chat_json(self, prompt: str, schema_hint: Optional[str] = None) -> Dict[str, Any]:
        """Ask GPT for structured JSON and return a parsed dict."""
        instruction = prompt
        if schema_hint:
            instruction += f"\n\nReturn JSON matching this shape:\n{schema_hint}"
        raw = self._create(
            [
                {"role": "system",
                 "content": "You output ONLY valid JSON. No prose, no fences."},
                {"role": "user", "content": instruction},
            ],
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GPTConnectorError(f"GPT returned invalid JSON: {raw[:200]}") from exc

    def embed(self, texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
        """Get embeddings (useful for the syntropic miner / recognition cascade)."""
        resp = self._client.embeddings.create(model=model, input=texts)
        return [item.embedding for item in resp.data]


# ---------------------------------------------------------------------- #
# CLI
# ---------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Connect to OpenAI GPT")
    parser.add_argument("prompt", nargs="*", help="Prompt text")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true", help="Request JSON output")
    parser.add_argument("--test", action="store_true", help="Connectivity smoke test")
    args = parser.parse_args()

    try:
        gpt = GPTConnector(model=args.model)
    except GPTConnectorError as exc:
        print(f"SETUP ERROR: {exc}", file=sys.stderr)
        return 2

    if args.test:
        reply = gpt.chat("Reply with exactly: CONNECTION_OK", temperature=0)
        print(f"Model {args.model} responded: {reply.strip()}")
        return 0 if "CONNECTION_OK" in reply else 1

    prompt = " ".join(args.prompt)
    if not prompt:
        parser.print_help()
        return 2

    if args.json:
        print(json.dumps(gpt.chat_json(prompt), indent=2))
    else:
        print(gpt.chat(prompt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
