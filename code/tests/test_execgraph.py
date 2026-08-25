"""Tests for execution graphs: routing, checkpointing, interrupts (Module 9 L4)."""

import tempfile
import unittest
from pathlib import Path

from ce.execgraph import (
    END, Checkpointer, GraphError, IdempotencyLedger, Interrupted, StateGraph,
    chain_reliability, route,
)


def build_review_graph(fail_times: int = 0) -> tuple[StateGraph, dict]:
    calls = {"tests": 0, "merged": 0, "notified": 0}

    def analyze(s):
        return {"findings": ["f1"]}

    def run_tests(s):
        calls["tests"] += 1
        return {"tests_passed": calls["tests"] > fail_times, "attempts": s.get("attempts", 0) + 1}

    def fix(s):
        return {"findings": s["findings"] + ["fix"]}

    def merge(s):
        calls["merged"] += 1
        return {"merged": True}

    def notify(s):
        calls["notified"] += 1
        return {"notified": True}

    @route("merge", "fix", "escalate")
    def after_tests(s):
        if s.get("tests_passed"):
            return "merge"
        return "fix" if s.get("attempts", 0) < 3 else "escalate"

    g = StateGraph("analyze")
    g.add_node("analyze", analyze)
    g.add_node("run_tests", run_tests)
    g.add_node("fix", fix)
    g.add_node("merge", merge, idempotency_key=lambda s: "merge-pr-1", interrupt_before=True)
    g.add_node("notify", notify, idempotency_key=lambda s: "notify-pr-1")
    g.add_node("escalate", lambda s: {"escalated": True})
    g.add_edge("analyze", "run_tests")
    g.add_conditional_edges("run_tests", after_tests)
    g.add_edge("fix", "run_tests")
    g.add_edge("merge", "notify")
    g.add_edge("notify", END)
    g.add_edge("escalate", END)
    return g, calls


class TestRouting(unittest.TestCase):
    def test_routing_is_a_pure_function_testable_in_isolation(self):
        """In a loop this logic is buried in the iteration body."""
        _, _ = build_review_graph()

        @route("merge", "fix", "escalate")
        def after_tests(s):
            if s.get("tests_passed"):
                return "merge"
            return "fix" if s.get("attempts", 0) < 3 else "escalate"

        self.assertEqual(after_tests({"tests_passed": True}), "merge")
        self.assertEqual(after_tests({"tests_passed": False, "attempts": 1}), "fix")
        self.assertEqual(after_tests({"tests_passed": False, "attempts": 3}), "escalate")

    def test_cycle_terminates_via_the_routing_function(self):
        g, calls = build_review_graph(fail_times=2)
        out = g.run({"diff": "d"}, approvals={"merge": True})
        self.assertTrue(out["merged"])
        self.assertEqual(calls["tests"], 3)

    def test_exhausted_retries_reach_a_real_terminal_state(self):
        g, _ = build_review_graph(fail_times=99)
        out = g.run({"diff": "d"}, approvals={"merge": True})
        self.assertTrue(out.get("escalated"))
        self.assertNotIn("merged", out)


class TestStaticAnalysis(unittest.TestCase):
    def test_a_valid_graph_reports_no_problems(self):
        g, _ = build_review_graph()
        self.assertEqual(g.validate(), [])

    def test_dead_end_node_is_caught_before_running(self):
        g = StateGraph("a")
        g.add_node("a", lambda s: {})
        g.add_node("orphan", lambda s: {})
        g.add_edge("a", END)
        problems = " ".join(g.validate())
        self.assertIn("orphan", problems)
        self.assertIn("dead end", problems)

    def test_unreachable_node_is_caught(self):
        g = StateGraph("a")
        g.add_node("a", lambda s: {})
        g.add_node("island", lambda s: {})
        g.add_edge("a", END)
        g.add_edge("island", END)
        self.assertIn("unreachable", " ".join(g.validate()))

    def test_undeclared_route_targets_make_topology_opaque(self):
        """Without @route the graph cannot be statically analyzed -- which also
        means a meta-agent cannot reason about it (Module 9, Lesson 6)."""
        g = StateGraph("a")
        g.add_node("a", lambda s: {})
        g.add_node("b", lambda s: {})
        g.add_conditional_edges("a", lambda s: "b")   # no @route
        g.add_edge("b", END)
        self.assertIn("unreachable", " ".join(g.validate()))


class TestDurableExecution(unittest.TestCase):
    def test_crash_resumes_from_the_last_node_not_the_start(self):
        cp = Checkpointer()
        calls = {"n": 0}

        def counting(s):
            calls["n"] += 1
            return {"count": calls["n"]}

        def boom(s):
            raise RuntimeError("process killed")

        g = StateGraph("first")
        g.add_node("first", counting)
        g.add_node("second", boom)
        g.add_edge("first", "second")
        g.add_edge("second", END)

        with self.assertRaises(RuntimeError):
            g.run({}, run_id="r1", checkpointer=cp)
        self.assertEqual(calls["n"], 1)

        saved = cp.load("r1")
        self.assertEqual(saved["next_node"], "second")   # not back to "first"

    def test_checkpoints_persist_to_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            cp = Checkpointer(Path(tmp))
            g = StateGraph("a")
            g.add_node("a", lambda s: {"done": True})
            g.add_edge("a", END)
            g.run({"x": 1}, run_id="run-42", checkpointer=cp)
            self.assertTrue((Path(tmp) / "run-42.json").exists())
            self.assertTrue(Checkpointer(Path(tmp)).load("run-42")["state"]["done"])


class TestInterrupts(unittest.TestCase):
    def test_a_human_gate_genuinely_suspends_the_run(self):
        cp = Checkpointer()
        g, calls = build_review_graph()
        with self.assertRaises(Interrupted) as ctx:
            g.run({"diff": "d"}, run_id="pr1", checkpointer=cp)
        self.assertEqual(ctx.exception.node, "merge")
        self.assertEqual(calls["merged"], 0)          # nothing irreversible happened

    def test_approval_days_later_resumes_the_same_run(self):
        cp = Checkpointer()
        g, calls = build_review_graph()
        with self.assertRaises(Interrupted):
            g.run({"diff": "d"}, run_id="pr1", checkpointer=cp)
        # ... process exits, three days pass, approval arrives ...
        out = g.run({}, run_id="pr1", checkpointer=cp, resume=True, approvals={"merge": True})
        self.assertTrue(out["merged"])
        self.assertEqual(calls["merged"], 1)


class TestIdempotenceFencing(unittest.TestCase):
    """The dangerous window is when the process dies AFTER the side effect landed
    but BEFORE the checkpoint was written. A fence stored inside that checkpoint
    is not there when you need it — which is why the ledger is separate."""

    def test_effect_does_not_repeat_when_the_checkpoint_never_wrote(self):
        cp = Checkpointer()
        ledger = IdempotencyLedger()
        charges = {"n": 0}

        class DyingCheckpointer(Checkpointer):
            """Simulates the process dying right after a node's side effect."""

            def __init__(self, inner, die_after):
                super().__init__()
                self.inner, self.die_after, self.armed = inner, die_after, True

            def save(self, run_id, state, next_node, completed):
                if self.armed and self.die_after in " ".join(completed):
                    self.armed = False
                    raise SystemExit("process killed before checkpoint write")
                self.inner.save(run_id, state, next_node, completed)

            def load(self, run_id):
                return self.inner.load(run_id)

        def charge(s):
            charges["n"] += 1
            return {"charged": True}

        g = StateGraph("prepare")
        g.add_node("prepare", lambda s: {"ready": True})
        g.add_node("charge", charge,
                   idempotency_key=lambda s: "order-77",
                   on_skip=lambda s: {"charged": True})
        g.add_node("confirm", lambda s: {"confirmed": True})
        g.add_edge("prepare", "charge")
        g.add_edge("charge", "confirm")
        g.add_edge("confirm", END)

        dying = DyingCheckpointer(cp, die_after="charge")
        with self.assertRaises(SystemExit):
            g.run({}, run_id="o77", checkpointer=dying, ledger=ledger)
        self.assertEqual(charges["n"], 1)               # the card WAS charged

        # The checkpoint says we are still at "charge" -- it never recorded success.
        self.assertEqual(cp.load("o77")["next_node"], "charge")

        # Resume. Without the ledger this charges a second time.
        out = g.run({}, run_id="o77", checkpointer=cp, ledger=ledger, resume=True)
        self.assertEqual(charges["n"], 1)               # NOT 2
        self.assertTrue(out["charged"])                 # on_skip filled the state
        self.assertTrue(out["confirmed"])

    def test_without_a_ledger_the_effect_repeats(self):
        """The contrast. Same graph, no ledger, same crash -- charged twice."""
        cp = Checkpointer()
        charges = {"n": 0}
        fail = {"armed": True}

        def charge(s):
            charges["n"] += 1
            return {"charged": True}

        def confirm(s):
            if fail["armed"]:
                fail["armed"] = False
                raise RuntimeError("downstream died before checkpoint")
            return {"confirmed": True}

        g = StateGraph("charge")
        g.add_node("charge", charge, idempotency_key=lambda s: "order-88")
        g.add_node("confirm", confirm)
        g.add_edge("charge", "confirm")
        g.add_edge("confirm", END)

        # No checkpointer at all -- resume must start from the beginning.
        with self.assertRaises(RuntimeError):
            g.run({}, run_id="o88")
        g.run({}, run_id="o88")
        self.assertEqual(charges["n"], 2)               # the failure being prevented

    def test_resume_lets_the_caller_patch_state(self):
        """A resume after fixing an environment problem must accept new inputs,
        or the run fails identically forever."""
        cp = Checkpointer()

        def gate(s):
            if not s.get("api_key"):
                raise RuntimeError("missing credential")
            return {"ok": True}

        g = StateGraph("gate")
        g.add_node("gate", gate)
        g.add_edge("gate", END)

        with self.assertRaises(RuntimeError):
            g.run({"job": 1}, run_id="j", checkpointer=cp)
        out = g.run({"api_key": "set-now"}, run_id="j", checkpointer=cp, resume=True)
        self.assertTrue(out["ok"])
        self.assertEqual(out["job"], 1)                 # saved state preserved


class TestStopRule(unittest.TestCase):
    def test_long_chains_fail_on_arithmetic_not_agent_quality(self):
        self.assertAlmostEqual(chain_reliability(0.92, 9), 0.472, places=3)
        self.assertAlmostEqual(chain_reliability(0.92, 3), 0.779, places=3)

    def test_shortening_can_beat_improving(self):
        """Three steps at 92% beats nine steps at 95% -- shortening the chain
        outperforms a 3-point per-step improvement.

        Note it does NOT beat nine steps at 98%: topology is powerful, not magic.
        The lesson is that restructuring is usually cheaper than a 6-point
        per-step gain, not that per-step quality is irrelevant.
        """
        self.assertGreater(chain_reliability(0.92, 3), chain_reliability(0.95, 9))
        self.assertLess(chain_reliability(0.92, 3), chain_reliability(0.98, 9))

    def test_unterminated_cycle_hits_the_step_limit(self):
        g = StateGraph("a")
        g.add_node("a", lambda s: {})
        g.add_node("b", lambda s: {})
        g.add_edge("a", "b")
        g.add_edge("b", "a")
        with self.assertRaises(GraphError) as ctx:
            g.run({}, max_steps=20)
        self.assertIn("step limit", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
