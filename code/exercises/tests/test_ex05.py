import unittest

from ce import AgentLoop, Deterministic, MockModel, ModelResponse, ToolRegistry, call, say
from exercises._loader import load

ex = load("ex05_guardrails")

NEVER = Deterministic(lambda s: False, "never met")


def registry():
    reg = ToolRegistry()

    @reg.register("probe", "Probes.", {})
    def probe() -> str:
        return "same result every time"

    return reg


def run(model):
    loop = AgentLoop(model=model, tools=registry(), verifier=NEVER,
                     guardrails=ex.unattended_guardrails())
    return loop.run("investigate the thing")


class TestGuardrails(unittest.TestCase):
    def test_a_stuck_model_stops_immediately_not_eventually(self):
        outcome = run(MockModel(policy=lambda t, m: say("still thinking...")))
        self.assertFalse(outcome.ok)
        self.assertLessEqual(outcome.iterations, 6,
                             "no-progress detection should fire within a few iterations")
        self.assertIn("progress", outcome.reason)

    def test_a_thrashing_model_is_bounded(self):
        outcome = run(MockModel(policy=lambda t, m: call("probe")))
        self.assertFalse(outcome.ok)
        self.assertLess(outcome.iterations, 40)

    def test_a_runaway_model_hits_the_token_ceiling(self):
        big = ModelResponse(text="x" * 200_000, input_tokens=20_000, output_tokens=50_000)
        outcome = run(MockModel(policy=lambda t, m: big))
        self.assertFalse(outcome.ok)
        self.assertIn("token", outcome.reason.lower())
        self.assertLess(outcome.trace.total_tokens, 300_000)

    def test_every_exit_carries_a_reason_for_the_human(self):
        outcome = run(MockModel(policy=lambda t, m: say("hmm")))
        self.assertTrue(outcome.reason)
        self.assertEqual(outcome.status, "escalated")


if __name__ == "__main__":
    unittest.main()
