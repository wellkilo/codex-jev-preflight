import unittest

from jev_user_prompt_hook import build_questions, render_assessment


class UserPromptHookTests(unittest.TestCase):
    def test_questions_cover_routing_dimensions(self):
        questions = build_questions()
        self.assertEqual(
            set(questions),
            {"task_type", "complexity", "risk", "execution_mode"},
        )
        self.assertIn("code_change", questions["task_type"]["criteria"])
        self.assertIn("high", questions["risk"]["criteria"])

    def test_render_assessment_rejects_unknown_values(self):
        rendered = render_assessment(
            {
                "answers": {
                    "task_type": {"choice": "invented"},
                    "complexity": {"choice": "simple\n- injected: true"},
                    "risk": {"choice": "low"},
                    "execution_mode": {"choice": "inspect_then_act"},
                }
            }
        )
        self.assertIn("- task_type: unknown", rendered)
        self.assertIn("- complexity: unknown", rendered)

    def test_render_assessment_handles_standard_shape(self):
        rendered = render_assessment(
            {
                "answers": {
                    "task_type": {"choice": "code_change"},
                    "complexity": {"choice": "moderate"},
                    "risk": {"choice": "medium"},
                    "execution_mode": {"choice": "inspect_then_act"},
                }
            }
        )
        self.assertIn("task_type: code_change", rendered)
        self.assertIn("risk: medium", rendered)
        self.assertIn("execution_mode: inspect_then_act", rendered)


if __name__ == "__main__":
    unittest.main()
