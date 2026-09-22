import unittest

from jev_agent import ActionCandidate, ActionDecision, BrowserJevWorkflow
from jev_agent.browser_workflow import (
    FALLBACK_REASON_JEV_UNAVAILABLE,
    FALLBACK_REASON_LOW_CONFIDENCE,
    parse_action_decision,
)


class FakeClient:
    def __init__(self, available=True, response=None, error=None):
        self.available = available
        self.response = response
        self.error = error
        self.calls = 0

    def is_available(self):
        return self.available

    def judge(self, state, questions, timeout=None):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


class BrowserWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.candidates = [
            ActionCandidate("refund", "申请退款", role="button"),
            ActionCandidate("cancel", "取消订单", role="button", dangerous=True),
        ]

    def test_high_confidence_jev_decision_is_used(self):
        client = FakeClient(
            response={
                "answers": {
                    "next_action": {
                        "choice": {"key": "refund", "confidence": 0.91},
                        "reason": "matches the user's request",
                    }
                }
            }
        )
        workflow = BrowserJevWorkflow(client)
        decision = workflow.decide_next_action("state", self.candidates)

        self.assertEqual(decision.key, "refund")
        self.assertEqual(decision.source, "jev")
        self.assertAlmostEqual(decision.confidence, 0.91)
        self.assertEqual(client.calls, 1)

    def test_low_confidence_uses_llm_fallback(self):
        client = FakeClient(
            response={"answers": {"next_action": {"choice": "refund", "confidence": 0.55}}}
        )
        reasons = []

        def fallback(state, candidates, reason):
            reasons.append(reason)
            return ActionDecision("cancel", 0.95, "llm")

        workflow = BrowserJevWorkflow(client, fallback_decider=fallback)
        decision = workflow.decide_next_action("state", self.candidates)

        self.assertEqual(decision.source, "llm")
        self.assertEqual(decision.key, "cancel")
        self.assertEqual(reasons, [FALLBACK_REASON_LOW_CONFIDENCE])

    def test_exhausted_jev_uses_llm_without_calling_api(self):
        client = FakeClient(available=False)
        reasons = []

        def fallback(state, candidates, reason):
            reasons.append(reason)
            return ActionDecision("refund", 0.8, "llm")

        workflow = BrowserJevWorkflow(client, fallback_decider=fallback)
        decision = workflow.decide_next_action("state", self.candidates)

        self.assertEqual(decision.key, "refund")
        self.assertEqual(client.calls, 0)
        self.assertEqual(reasons, [FALLBACK_REASON_JEV_UNAVAILABLE])

    def test_missing_confidence_requires_fallback(self):
        client = FakeClient(response={"answers": {"next_action": {"choice": "refund"}}})
        workflow = BrowserJevWorkflow(
            client,
            fallback_decider=lambda state, candidates, reason: ActionDecision("refund", 0.8, "llm"),
        )
        decision = workflow.decide_next_action("state", self.candidates)
        self.assertEqual(decision.source, "llm")

    def test_parser_rejects_unknown_or_disabled_key(self):
        unknown = parse_action_decision(
            {"answers": {"next_action": {"choice": "invented", "confidence": 1}}},
            {"refund": self.candidates[0]},
        )
        disabled = parse_action_decision(
            {"answers": {"next_action": {"choice": "refund", "confidence": 1}}},
            {"refund": ActionCandidate("refund", "退款", disabled=True)},
        )
        self.assertIsNone(unknown)
        self.assertIsNone(disabled)


if __name__ == "__main__":
    unittest.main()
