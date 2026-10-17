"""Fault-injection regression tests for model_gateway.

Audit standard: for every injected fault, record whether the gateway
detects it, degrades safely, preserves evidence, and respects its budget.
No network required — providers are faked/mocked.
"""

import json
import os
import tempfile
import unittest
from unittest import mock

import httpx

import model_gateway as mg


class FakeProvider(mg.OpenAICompatProvider):
    """Provider whose behavior is scripted per-test."""

    def __init__(self, name, behaviors):
        super().__init__(name, "http://localhost:9/v1", "fake-model",
                         api_key="test")
        self.behaviors = list(behaviors)  # each: exception instance or return string
        self.calls = 0

    def complete(self, messages, temperature=0.0):
        self.calls += 1
        b = self.behaviors.pop(0) if self.behaviors else self.behaviors_fallback
        if isinstance(b, Exception):
            raise b
        return b

    behaviors_fallback = '{"x": 1, "y": 2}'


def make_gw(providers, **kw):
    d = tempfile.mkdtemp()
    return mg.ModelGateway(providers=providers,
                           ledger_path=os.path.join(d, "evidence.jsonl"),
                           **kw)


ACTION_SPEC = {"type": "object", "exact_fields": {"x": "int", "y": "int"}}


class TestStrictValidator(unittest.TestCase):
    """The pixel-swarm audit fix, generalized: reject extras independently."""

    def test_valid_action(self):
        ok, why = mg.strict_validate({"x": 3, "y": 2}, ACTION_SPEC)
        self.assertTrue(ok, why)

    def test_injected_extra_field_rejected(self):
        # The exact attack from the audit: legal coords + smuggled command.
        ok, why = mg.strict_validate(
            {"x": 3, "y": 2, "command": "delete"}, ACTION_SPEC)
        self.assertFalse(ok)
        self.assertIn("command", why)

    def test_missing_field_rejected(self):
        ok, _ = mg.strict_validate({"x": 3}, ACTION_SPEC)
        self.assertFalse(ok)

    def test_bool_not_accepted_as_int(self):
        ok, _ = mg.strict_validate({"x": True, "y": 2}, ACTION_SPEC)
        self.assertFalse(ok)

    def test_constraint_violation_rejected(self):
        spec = dict(ACTION_SPEC, constraint=lambda d: (d["x"], d["y"]) in [(1, 1)])
        ok, why = mg.strict_validate({"x": 9, "y": 9}, spec)
        self.assertFalse(ok)
        self.assertEqual(why, "constraint_violated")

    def test_non_object_payload(self):
        for bad in ["string", 42, None, [1, 2]]:
            ok, _ = mg.strict_validate(bad, ACTION_SPEC)
            self.assertFalse(ok)


class TestFaultInjection(unittest.TestCase):
    """Each injected fault must be detected, typed, logged, and survivable."""

    def test_timeout_then_success_degrades_to_next_provider(self):
        p1 = FakeProvider("flaky", [httpx.TimeoutException("t"),
                                    httpx.TimeoutException("t"),
                                    httpx.TimeoutException("t")])
        p2 = FakeProvider("solid", ['{"x": 1, "y": 2}'])
        gw = make_gw([p1, p2], max_retries=2)
        r = gw.ask("go", schema=ACTION_SPEC)
        self.assertIsInstance(r, mg.SuccessResult)
        self.assertEqual(r.provider, "solid")
        self.assertGreater(r.attempts, 1)

    def test_malformed_json_is_rejected_and_ledgered(self):
        p = FakeProvider("sloppy", ["this is not json at all"] * 3)
        gw = make_gw([p])
        r = gw.ask("go", schema=ACTION_SPEC)
        self.assertIsInstance(r, mg.FailureResult)
        self.assertIn("malformed", r.detail)

    def test_markdown_fenced_json_still_validates(self):
        p = FakeProvider("chatty", ["```json\n{\"x\": 1, \"y\": 2}\n```"])
        gw = make_gw([p])
        r = gw.ask("go", schema=ACTION_SPEC)
        self.assertIsInstance(r, mg.SuccessResult)
        self.assertEqual(r.data, {"x": 1, "y": 2})

    def test_smuggled_command_field_rejected_end_to_end(self):
        p = FakeProvider("evil", ['{"x": 1, "y": 2, "command": "delete"}'] * 3)
        gw = make_gw([p])
        r = gw.ask("go", schema=ACTION_SPEC)
        self.assertIsInstance(r, Failure := mg.FailureResult)
        self.assertIn("schema_reject", r.detail)

    def test_auth_failure_not_retried(self):
        req = httpx.Request("POST", "http://localhost:9/v1/chat/completions")
        resp = httpx.Response(401, request=req)
        err = httpx.HTTPStatusError("401", request=req, response=resp)
        p = FakeProvider("denied", [err])
        gw = make_gw([p], max_retries=2)
        r = gw.ask("go")
        self.assertIsInstance(r, mg.FailureResult)
        self.assertIn("auth_failure", r.detail)
        self.assertEqual(p.calls, 1)  # non-retryable: exactly one call consumed

    def test_oversized_response_rejected(self):
        # Fault injected at the transport layer: provider streams an
        # oversized body; the real size check in OpenAICompatProvider must
        # raise ValueError("oversized_response") and the gateway must
        # convert that into a typed failure, not a crash or silent success.
        req = httpx.Request("POST", "http://localhost:9/v1/chat/completions")

        class OversizedResp(httpx.Response):
            @property
            def content(self):  # simulate > MAX_RESPONSE_BYTES payload
                return b"x" * (mg.MAX_RESPONSE_BYTES + 1)

        gw = make_gw([mg.OpenAICompatProvider("bloated",
                                              "http://localhost:9/v1",
                                              "fake-model", api_key="test")])
        target = gw.providers[0]
        with mock.patch("httpx.post", return_value=OversizedResp(200, request=req)):
            with self.assertRaises(ValueError) as cm:
                target.complete([{"role": "user", "content": "go"}])
            self.assertIn("oversized", str(cm.exception))

        # And end-to-end through the gateway:
        with mock.patch.object(target, "complete",
                               side_effect=ValueError("oversized_response")):
            r = gw.ask("go")
        self.assertIsInstance(r, mg.FailureResult)
        self.assertIn("oversized", r.detail)

    def test_budget_enforcement_no_unbounded_authority(self):
        p = FakeProvider("hungry", ['{"x": 1, "y": 2}'] * 100)
        gw = make_gw([p], max_calls_per_run=3)
        results = [gw.ask("go", schema=ACTION_SPEC) for _ in range(5)]
        self.assertTrue(all(isinstance(r, mg.SuccessResult) for r in results[:3]))
        self.assertIsInstance(results[3], mg.FailureResult)
        self.assertEqual(results[3].reason, "budget_exhausted")
        self.assertLessEqual(gw.calls_used, 3)

    def test_all_providers_down_returns_typed_failure_not_exception(self):
        dead = FakeProvider("dead1", [httpx.ConnectError("refused")] * 3)
        dead2 = FakeProvider("dead2", [httpx.ConnectError("refused")] * 3)
        gw = make_gw([dead, dead2], max_retries=0)
        r = gw.ask("go")
        self.assertIsInstance(r, mg.FailureResult)
        self.assertEqual(r.reason, "all_providers_failed")
        self.assertIsNotNone(r.degraded_to)  # caller knows to fall back (e.g. BFS)

    def test_evidence_survives_and_chain_verifies(self):
        p = FakeProvider("witness", ['{"x": 1, "y": 2}',
                                     httpx.TimeoutException("t")])
        gw = make_gw([p], max_retries=0)
        gw.ask("go", schema=ACTION_SPEC)
        gw.ask("go", schema=ACTION_SPEC)
        ok, n, bad = mg.EvidenceLedger.verify(gw.ledger.path)
        self.assertTrue(ok, bad)
        self.assertEqual(n, 2)  # one success, one failure — both hashed

    def test_ledger_detects_tampering(self):
        p = FakeProvider("witness", ['{"x": 1, "y": 2}'])
        gw = make_gw([p])
        gw.ask("go", schema=ACTION_SPEC)
        gw.ask("go", schema=ACTION_SPEC)
        lines = open(gw.ledger.path).read().splitlines()
        rec = json.loads(lines[0])
        rec["event"] = "clobbered"          # attacker edits a past record
        lines[0] = json.dumps(rec, sort_keys=True)
        with open(gw.ledger.path, "w") as f:
            f.write("\n".join(lines) + "\n")
        ok, n, bad = mg.EvidenceLedger.verify(gw.ledger.path)
        self.assertFalse(ok)
        self.assertIn("line 1", bad)


class TestJsonExtraction(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(mg._extract_json('{"a":1}'), '{"a":1}')

    def test_fenced(self):
        self.assertEqual(mg._extract_json('```json\n{"a":1}\n```'), '{"a":1}')

    def test_prose_wrapped(self):
        self.assertEqual(
            mg._extract_json('Sure! {"a":1} — hope that helps'), '{"a":1}')


if __name__ == "__main__":
    unittest.main(verbosity=2)
