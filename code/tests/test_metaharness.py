"""Tests for the meta-harness loop (Module 9, Lessons 6-7).

These are mostly tests that FAILURE MODES are caught, because that is what the
lesson is about: the success path is easy and the pathologies are quiet.
"""

import unittest

from ce.metaharness import (
    DEFAULT_FROZEN, Archive, Candidate, FailureSignature, FrozenSurfaceError,
    HeldOutGate, MetaHarness, Scores, mine_weaknesses,
)


class TestWeaknessMining(unittest.TestCase):
    def test_failures_cluster_by_mechanism_not_error_code(self):
        """Twenty TimeoutErrors may be three unrelated problems."""
        failures = (
            [{"err": "TimeoutError", "cause": "search_loop"}] * 5
            + [{"err": "TimeoutError", "cause": "slow_tool"}] * 5
            + [{"err": "TimeoutError", "cause": "retry_storm"}] * 10
        )

        def classify(f):
            mechanisms = {
                "search_loop": ("thrashed on search, never converged", "tool_descriptions"),
                "slow_tool": ("blocked on a slow upstream call", "timeouts"),
                "retry_storm": ("retried without backoff until the budget died", "retry_policy"),
            }
            mech, surface = mechanisms[f["cause"]]
            return FailureSignature(f["err"], f["cause"], mech, surface=surface)

        signatures = mine_weaknesses(failures, classify=classify)
        self.assertEqual(len(signatures), 3)               # not 1
        self.assertEqual(signatures[0].count, 10)          # ranked by frequency
        self.assertEqual(len({s.surface for s in signatures}), 3)

    def test_signature_id_is_stable_across_runs(self):
        a = FailureSignature("E", "b", "same mechanism")
        b = FailureSignature("OTHER", "different", "same mechanism")
        self.assertEqual(a.id, b.id)     # keyed on mechanism alone


class TestHeldOutGate(unittest.TestCase):
    def setUp(self):
        self.gate = HeldOutGate()
        self.base = Scores(held_in=0.70, held_out=0.70)

    def test_a_genuine_improvement_is_accepted(self):
        v = self.gate.judge(self.base, Scores(0.78, 0.76))
        self.assertTrue(v.accepted)

    def test_fitting_the_held_in_split_is_caught(self):
        """The whole point of the gate: big held-in gain, no held-out gain."""
        v = self.gate.judge(self.base, Scores(held_in=0.85, held_out=0.705))
        self.assertFalse(v.accepted)
        self.assertIn("learning your evaluator", v.reason)

    def test_held_out_regression_is_refused_even_with_a_big_held_in_gain(self):
        v = self.gate.judge(self.base, Scores(held_in=0.90, held_out=0.68))
        self.assertFalse(v.accepted)
        self.assertIn("held-out regression", v.reason)

    def test_noise_is_not_an_improvement(self):
        v = self.gate.judge(self.base, Scores(0.7005, 0.7002))
        self.assertFalse(v.accepted)
        self.assertIn("no material gain", v.reason)

    def test_for_split_derives_min_gain_from_sample_size(self):
        """min_gain=0.005 on a 200-case split is ONE flipped case — a coin toss.

        A loop running hundreds of rounds against a gate that accepts
        single-case deltas accumulates noise as 'improvement', which is the
        Lesson 5 pathology enabled by a default. for_split() demands several
        net case-flips instead.
        """
        gate = HeldOutGate.for_split(200)                 # default: 3 net flips
        self.assertAlmostEqual(gate.min_gain, 0.015)
        base = Scores(0.70, 0.70)
        one_flip = Scores(0.705, 0.705)                   # 1 case of 200
        self.assertFalse(gate.judge(base, one_flip).accepted)
        four_flips = Scores(0.72, 0.72)
        self.assertTrue(gate.judge(base, four_flips).accepted)

    def test_for_split_refuses_a_meaningless_split(self):
        with self.assertRaises(ValueError):
            HeldOutGate.for_split(0)

    def test_catastrophic_forgetting_hides_behind_the_mean(self):
        """The aggregate improved. One task family collapsed."""
        base = Scores(0.70, 0.70, per_category={"invoices": 0.80, "contracts": 0.60})
        cand = Scores(0.76, 0.75, per_category={"invoices": 0.95, "contracts": 0.40})
        v = self.gate.judge(base, cand)
        self.assertFalse(v.accepted)
        self.assertIn("contracts", v.reason)
        self.assertIn("per-category regression", v.reason)
        self.assertEqual(v.regressions, ("contracts",))


class TestFrozenSurfaces(unittest.TestCase):
    def _mh(self, editable):
        return MetaHarness(editable=frozenset(editable), evaluate=lambda h: Scores(0.5, 0.5))

    def test_editing_the_exam_is_refused(self):
        mh = self._mh({"system_prompt"})
        with self.assertRaises(FrozenSurfaceError) as ctx:
            mh.check_surface(Candidate("eval_data", "easier cases"))
        self.assertIn("frozen surface", str(ctx.exception))

    def test_every_default_frozen_surface_is_refused(self):
        mh = self._mh({"system_prompt"})
        for surface in DEFAULT_FROZEN:
            with self.assertRaises(FrozenSurfaceError):
                mh.check_surface(Candidate(surface, "anything"))

    def test_undeclared_surfaces_are_refused_too(self):
        """Not-frozen is not the same as editable."""
        mh = self._mh({"system_prompt"})
        with self.assertRaises(FrozenSurfaceError):
            mh.check_surface(Candidate("tool_implementations", "..."))

    def test_declaring_a_surface_both_editable_and_frozen_fails_loudly(self):
        with self.assertRaises(FrozenSurfaceError):
            MetaHarness(editable=frozenset({"permissions"}), evaluate=lambda h: Scores(0, 0))

    def test_a_frozen_proposal_never_reaches_evaluation(self):
        evaluated = []
        mh = MetaHarness(
            editable=frozenset({"system_prompt"}),
            evaluate=lambda h: (evaluated.append(h), Scores(0.99, 0.99))[1],
        )
        with self.assertRaises(FrozenSurfaceError):
            mh.step({}, Candidate("permissions", "grant all"), Scores(0.5, 0.5))
        self.assertEqual(evaluated, [])    # refused before it could score well


class TestArchive(unittest.TestCase):
    def test_rejections_are_kept_as_context(self):
        a = Archive()
        gate = HeldOutGate()
        base = Scores(0.7, 0.7)
        a.record(Candidate("p", "good"), gate.judge(base, Scores(0.78, 0.77)))
        a.record(Candidate("p", "bad"), gate.judge(base, Scores(0.85, 0.70)))
        self.assertEqual(len(a.accepted), 1)
        self.assertEqual(len(a.rejected), 1)
        self.assertIn("learning your evaluator", a.rejected[0][1].reason)

    def test_diversity_collapse_is_visible(self):
        a = Archive()
        gate, base = HeldOutGate(), Scores(0.7, 0.7)
        for i in range(5):
            a.record(Candidate("system_prompt", f"v{i}"),
                     gate.judge(base, Scores(0.75 + i / 100, 0.74 + i / 100)))
        self.assertLess(a.diversity(), 0.3)          # one surface, five edits

        a2 = Archive()
        for surface in ("system_prompt", "retry_policy", "tool_descriptions", "workflow"):
            a2.record(Candidate(surface, "x"), gate.judge(base, Scores(0.76, 0.75)))
        self.assertEqual(a2.diversity(), 1.0)

    def test_pareto_frontier_keeps_the_cheap_alternative(self):
        """Single-objective optimization on accuracy finds expensive wins."""
        a = Archive()
        gate, base = HeldOutGate(), Scores(0.70, 0.70)
        a.record(Candidate("p", "accurate+expensive"), gate.judge(base, Scores(0.80, 0.79, cost=9.0)))
        a.record(Candidate("p", "nearly-as-good+cheap"), gate.judge(base, Scores(0.79, 0.78, cost=1.0)))
        a.record(Candidate("p", "dominated"), gate.judge(base, Scores(0.76, 0.75, cost=5.0)))
        frontier = {c.edit for c, _ in a.pareto()}
        self.assertIn("accurate+expensive", frontier)
        self.assertIn("nearly-as-good+cheap", frontier)
        self.assertNotIn("dominated", frontier)


class TestOuterLoop(unittest.TestCase):
    def test_the_loop_stops_when_it_stops_improving(self):
        rounds = {"n": 0}

        def evaluate(harness):
            # Improves for the first two accepted edits, then flat.
            n = len(harness.get("system_prompt", ""))
            return Scores(held_in=0.70 + min(n, 2) * 0.05, held_out=0.70 + min(n, 2) * 0.045)

        def propose(harness, archive):
            rounds["n"] += 1
            return [Candidate("system_prompt", (harness.get("system_prompt", "") + "x"))]

        mh = MetaHarness(editable=frozenset({"system_prompt"}), evaluate=evaluate)
        final, scores = mh.run({}, propose, rounds=20, plateau_after=2)
        self.assertLess(rounds["n"], 20)              # terminated early
        self.assertGreater(scores.held_out, 0.70)

    def test_frozen_proposals_are_skipped_without_killing_the_run(self):
        def propose(harness, archive):
            return [Candidate("eval_data", "cheat"), Candidate("system_prompt", "legit")]

        mh = MetaHarness(
            editable=frozenset({"system_prompt"}),
            evaluate=lambda h: Scores(0.8, 0.79) if h.get("system_prompt") else Scores(0.7, 0.7),
        )
        final, scores = mh.run({}, propose, rounds=3, plateau_after=1)
        self.assertEqual(final.get("system_prompt"), "legit")
        self.assertNotIn("eval_data", final)


if __name__ == "__main__":
    unittest.main()
