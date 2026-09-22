import json
import tempfile
import unittest
from pathlib import Path

from jev_agent import JevClient, JevQuotaExhausted, JevUnavailable
from jev_agent.jev_client import HttpResponse


class FakeTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, headers, body, timeout):
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "json": json.loads(body.decode("utf-8")),
                "timeout": timeout,
            }
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class ManualClock:
    def __init__(self, now=1_000.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class JevClientTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.state_path = str(Path(self.tempdir.name) / "quota.json")
        self.clock = ManualClock()

    def tearDown(self):
        self.tempdir.cleanup()

    def make_client(self, transport, **kwargs):
        return JevClient(
            api_key="test-key",
            transport=transport,
            state_path=self.state_path,
            clock=self.clock,
            **kwargs,
        )

    def test_judge_builds_expected_request_and_returns_answers(self):
        transport = FakeTransport(
            HttpResponse(
                200,
                {"x-ratelimit-remaining": "2", "x-ratelimit-limit": "10"},
                json.dumps({"answers": {"next_action": {"choice": "ok"}}}).encode(),
            )
        )
        client = self.make_client(transport)
        result = client.judge("page state", {"next_action": {"type": "choice"}})

        self.assertEqual(result["answers"]["next_action"]["choice"], "ok")
        call = transport.calls[0]
        self.assertEqual(call["url"], "https://api.typesafe.ai/v1/systemone")
        self.assertEqual(call["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(call["json"]["model"], "jev-latest")
        self.assertEqual(call["json"]["state"], "page state")
        self.assertEqual(client.status()["remaining"], 2)

    def test_successful_last_request_opens_breaker_for_future_calls(self):
        transport = FakeTransport(
            HttpResponse(
                200,
                {"x-ratelimit-remaining": "0"},
                b'{"answers": {"next_action": {"choice": "ok"}}}',
            )
        )
        client = self.make_client(transport)
        client.judge("page", {"next_action": {"type": "choice"}})

        self.assertFalse(client.is_available())
        with self.assertRaises(JevQuotaExhausted):
            client.judge("page", {"next_action": {"type": "choice"}})
        self.assertEqual(len(transport.calls), 1)

    def test_relative_reset_header_is_respected(self):
        transport = FakeTransport(
            HttpResponse(
                200,
                {
                    "x-ratelimit-remaining": "0",
                    "x-ratelimit-reset": "60",
                },
                b'{"answers": {}}',
            ),
            HttpResponse(200, {}, b'{"answers": {}}'),
        )
        client = self.make_client(transport)
        client.judge("page", {"q": {"type": "choice"}})

        self.assertFalse(client.is_available())
        self.clock.advance(61)
        client.judge("page", {"q": {"type": "choice"}})
        self.assertEqual(len(transport.calls), 2)

    def test_http_402_is_persisted_across_clients(self):
        transport = FakeTransport(HttpResponse(402, {}, b'{"error": "payment required"}'))
        first = self.make_client(transport)
        with self.assertRaises(JevQuotaExhausted):
            first.judge("page", {"q": {"type": "choice"}})

        second = self.make_client(FakeTransport())
        self.assertFalse(second.is_available())
        self.assertEqual(second.status()["kind"], "quota")

    def test_rate_limit_is_temporary(self):
        transport = FakeTransport(
            HttpResponse(429, {"retry-after": "30"}, b'{"error": "rate limited"}'),
            HttpResponse(200, {}, b'{"answers": {}}'),
        )
        client = self.make_client(transport)
        with self.assertRaises(JevUnavailable):
            client.judge("page", {"q": {"type": "choice"}})
        self.assertEqual(client.status()["kind"], "temporary")

        self.clock.advance(31)
        self.assertTrue(client.is_available())
        client.judge("page", {"q": {"type": "choice"}})
        self.assertEqual(len(transport.calls), 2)

    def test_missing_api_key_does_not_call_transport(self):
        transport = FakeTransport()
        client = JevClient(
            api_key="",
            transport=transport,
            state_path=self.state_path,
            clock=self.clock,
        )
        with self.assertRaisesRegex(Exception, "TYPESAFE_API_KEY"):
            client.judge("page", {"q": {"type": "choice"}})
        self.assertEqual(transport.calls, [])


if __name__ == "__main__":
    unittest.main()
