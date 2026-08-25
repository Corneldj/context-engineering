"""Tests for typed, bi-temporal graphs (Module 9, Lessons 1-2)."""

import unittest

from ce.graph import (
    FOREVER, Edge, EdgeType, Graph, Node, OntologyError,
    hop_confidence, required_per_hop,
)


def build() -> Graph:
    g = Graph([
        EdgeType("owns", "Team", "Service", time_varying=True, accuracy=0.95),
        EdgeType("depends_on", "Service", "Service", accuracy=0.90),
        EdgeType("caused_by", "Incident", "Deploy", accuracy=0.85),
        EdgeType("touched", "Deploy", "Service", accuracy=0.98),
    ])
    for nid, ntype, name in [
        ("t_plat", "Team", "Platform"), ("t_pay", "Team", "Payments"),
        ("s_auth", "Service", "auth-lib"), ("s_api", "Service", "payments-api"),
        ("s_web", "Service", "web"), ("s_orphan", "Service", "legacy-cron"),
        ("i_7", "Incident", "INC-7"), ("d_412", "Deploy", "deploy-412"),
    ]:
        g.add_node(Node(nid, ntype, name))
    return g


class TestOntologyGate(unittest.TestCase):
    """Stage 7 of the pipeline is only possible because stage 3 declared a schema."""

    def test_undeclared_edge_type_is_refused(self):
        g = build()
        with self.assertRaises(OntologyError) as ctx:
            g.add_edge("t_plat", "is_associated_with", "s_auth")
        self.assertIn("Undeclared edge type", str(ctx.exception))

    def test_wrong_endpoint_type_is_refused(self):
        g = build()
        with self.assertRaises(OntologyError) as ctx:
            g.add_edge("s_auth", "owns", "s_api")     # a Service cannot own
        self.assertIn("expects a 'Team'", str(ctx.exception))

    def test_unknown_node_is_refused(self):
        g = build()
        with self.assertRaises(OntologyError):
            g.add_edge("t_plat", "owns", "s_nonexistent")


class TestBiTemporal(unittest.TestCase):
    def test_two_clocks_answer_different_questions(self):
        g = build()
        e = g.add_edge("t_plat", "owns", "s_api", t_valid=100, t_created=100)
        self.assertTrue(e.true_at(150))
        self.assertTrue(e.believed_at(150))
        self.assertFalse(e.true_at(50))

    def test_supersede_preserves_history(self):
        """Invalidate, never delete."""
        g = build()
        old = g.add_edge("t_plat", "owns", "s_api", t_valid=100, t_created=100)
        g.supersede(old, new_target="s_web", at=300)

        # Current state
        now = g.out_edges("t_plat", type="owns", at=400)
        self.assertEqual([e.target for e in now], ["s_web"])

        # Historical state — the old fact is still queryable
        then = g.out_edges("t_plat", type="owns", at=200)
        self.assertEqual([e.target for e in then], ["s_api"])

    def test_correction_changes_the_world_clock_not_the_belief_clock(self):
        """We learn the transfer actually happened earlier than recorded.

        The world-clock moves; the belief-clock records that we only found out
        now. 'What did we believe in March?' must still be answerable.
        """
        g = build()
        wrong = g.add_edge("t_plat", "owns", "s_api", t_valid=300, t_created=300)
        g.correct(wrong, actual_t_valid=200, discovered_at=400)

        # What was true in February (t=250)? Under corrected records: yes.
        self.assertTrue(any(e.true_at(250) for e in g.out_edges("t_plat", type="owns")))
        # What did we BELIEVE at t=350, before the correction? Not that.
        believed_then = g.out_edges("t_plat", type="owns", believed_at=350)
        self.assertTrue(all(e.t_valid == 300 for e in believed_then))

    def test_nothing_is_ever_removed_from_the_edge_list(self):
        g = build()
        e = g.add_edge("t_plat", "owns", "s_api", t_valid=100, t_created=100)
        before = len(g.edges)
        g.supersede(e, new_target="s_web", at=300)
        self.assertEqual(len(g.edges), before + 1)     # one closed, one added


class TestConfidenceDecay(unittest.TestCase):
    def test_the_arithmetic_that_kills_graph_projects(self):
        self.assertAlmostEqual(hop_confidence(0.85, 5), 0.4437, places=3)
        self.assertAlmostEqual(hop_confidence(0.95, 2), 0.9025, places=4)

    def test_required_per_hop_inverts_it(self):
        need = required_per_hop(0.95, 3)
        self.assertAlmostEqual(hop_confidence(need, 3), 0.95, places=6)
        self.assertGreater(need, 0.98)       # compliance-grade needs near-perfect extraction

    def test_traversal_confidence_compounds(self):
        g = build()
        g.add_edge("i_7", "caused_by", "d_412")        # 0.85
        g.add_edge("d_412", "touched", "s_api")        # 0.98
        paths = g.traverse("i_7", ["caused_by", "touched"])
        self.assertEqual(len(paths), 1)
        self.assertAlmostEqual(paths[0].confidence, 0.85 * 0.98, places=4)

    def test_low_confidence_paths_are_withheld_not_returned_flat(self):
        g = build()
        g.add_edge("i_7", "caused_by", "d_412")
        g.add_edge("d_412", "touched", "s_api")
        self.assertEqual(g.traverse("i_7", ["caused_by", "touched"], min_confidence=0.9), [])
        self.assertEqual(len(g.traverse("i_7", ["caused_by", "touched"], min_confidence=0.8)), 1)

    def test_path_explains_itself(self):
        g = build()
        g.add_edge("i_7", "caused_by", "d_412")
        g.add_edge("d_412", "touched", "s_api")
        explanation = g.traverse("i_7", ["caused_by", "touched"])[0].explain()
        self.assertIn("caused_by", explanation)
        self.assertIn("confidence", explanation)


class TestQueriesVectorSearchCannotAnswer(unittest.TestCase):
    def test_absence_query(self):
        """Similarity search can only find things that exist."""
        g = build()
        g.add_edge("t_plat", "owns", "s_auth")
        g.add_edge("t_pay", "owns", "s_api")
        g.add_edge("t_plat", "owns", "s_web")
        # "Which services have no owner?" asks about INCOMING owns edges.
        orphans = g.missing("Service", "owns", direction="in")
        self.assertEqual([n.id for n in orphans], ["s_orphan"])

    def test_absence_direction_matters(self):
        """Getting the direction wrong silently returns everything."""
        g = build()
        g.add_edge("t_plat", "owns", "s_auth")
        # No Service has an OUTGOING owns edge -- owns runs Team -> Service.
        self.assertEqual(len(g.missing("Service", "owns", direction="out")), 4)
        self.assertEqual(len(g.missing("Service", "owns", direction="in")), 3)

    def test_absence_query_is_time_scoped(self):
        """A service can lose its owner. The absence query must see that."""
        g = build()
        e = g.add_edge("t_plat", "owns", "s_api", t_valid=0, t_created=0)
        g.invalidate(e, t_invalid=500)
        self.assertNotIn("s_api", [n.id for n in g.missing("Service", "owns", at=100)])
        self.assertIn("s_api", [n.id for n in g.missing("Service", "owns", at=900)])

    def test_transitive_dependency_walk(self):
        g = build()
        g.add_edge("s_web", "depends_on", "s_api")
        g.add_edge("s_api", "depends_on", "s_auth")
        paths = g.transitive("s_web", "depends_on", max_hops=4)
        reached = {p.edges[-1].target for p in paths}
        self.assertEqual(reached, {"s_api", "s_auth"})

    def test_cycles_do_not_hang_the_traversal(self):
        g = build()
        g.add_edge("s_web", "depends_on", "s_api")
        g.add_edge("s_api", "depends_on", "s_web")     # circular dependency
        paths = g.transitive("s_web", "depends_on", max_hops=10)
        self.assertLessEqual(len(paths), 4)

    def test_time_scoped_traversal(self):
        g = build()
        e = g.add_edge("t_plat", "owns", "s_api", t_valid=0, t_created=0)
        g.supersede(e, new_target="s_web", at=500)
        self.assertEqual(len(g.traverse("t_plat", ["owns"], at=100)), 1)
        self.assertEqual(g.traverse("t_plat", ["owns"], at=100)[0].edges[0].target, "s_api")
        self.assertEqual(g.traverse("t_plat", ["owns"], at=900)[0].edges[0].target, "s_web")


if __name__ == "__main__":
    unittest.main()


class TestCorrectionBothDirections(unittest.TestCase):
    """A real correction usually moves BOTH clocks: the old owner's edge ends
    earlier AND the new owner's begins earlier. An API that can only correct
    the start of a fact cannot execute half of real-world corrections —
    including this module's own Lesson 2 exercise."""

    def test_correcting_when_a_fact_ended(self):
        g = build()
        e = g.add_edge("t_plat", "owns", "s_api", t_valid=0, t_created=0)
        closed = g.invalidate(e, t_invalid=300)          # recorded: ended in March
        g.correct(closed, actual_t_invalid=200, discovered_at=400)  # actually Feb

        # Truth now: Platform did NOT own it at t=250.
        self.assertFalse(any(e2.true_at(250) and e2.believed_at(500)
                             for e2 in g.out_edges("t_plat", type="owns")))
        # But in April we still BELIEVED it was owned until March.
        believed = [e2 for e2 in g.out_edges("t_plat", type="owns") if e2.believed_at(350)]
        self.assertTrue(any(e2.t_invalid == 300 for e2 in believed))

    def test_the_full_transfer_correction_from_lesson_2(self):
        """Transfer recorded at t=300, actually happened t=200, learned t=400.

        Note that we continue with the edges the mutating calls RETURN — the
        pre-mutation references are stale, and using one raises a clear error
        (tested below) rather than corrupting the graph.
        """
        g = build()
        a = g.add_edge("t_plat", "owns", "s_api", t_valid=0, t_created=0)
        a_closed = g.invalidate(a, t_invalid=300)
        b = g.add_edge("t_pay", "owns", "s_api", t_valid=300, t_created=300)
        # The correction, both halves:
        g.correct(a_closed, actual_t_invalid=200, discovered_at=400)
        g.correct(b, actual_t_valid=200, discovered_at=400)
        # Corrected truth at t=250: Payments owns it, Platform does not.
        owners_now = [e.source for e in g.edges
                      if e.type == "owns" and e.true_at(250) and e.believed_at(500)]
        self.assertEqual(owners_now, ["t_pay"])

    def test_a_stale_edge_reference_fails_loudly_not_silently(self):
        g = build()
        a = g.add_edge("t_plat", "owns", "s_api", t_valid=0, t_created=0)
        g.invalidate(a, t_invalid=300)          # `a` is now stale
        with self.assertRaises(ValueError) as ctx:
            g.correct(a, actual_t_invalid=200, discovered_at=400)
        self.assertIn("edge they returned", str(ctx.exception))

    def test_a_correction_with_nothing_to_correct_is_refused(self):
        g = build()
        e = g.add_edge("t_plat", "owns", "s_api", t_valid=0, t_created=0)
        with self.assertRaises(ValueError):
            g.correct(e, discovered_at=100)


class TestDiamondDeduplication(unittest.TestCase):
    def test_transitive_returns_one_path_per_target(self):
        """A diamond (A->B->D, A->C->D) must not report D twice."""
        g = Graph([EdgeType("dep", "S", "S", accuracy=0.9)])
        for x in "ABCD":
            g.add_node(Node(x, "S", x))
        for s, t in [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]:
            g.add_edge(s, "dep", t)
        paths = g.transitive("A", "dep")
        targets = [p.edges[-1].target for p in paths]
        self.assertEqual(sorted(targets), ["B", "C", "D"])   # D exactly once

    def test_the_kept_path_is_the_most_trustworthy_one(self):
        g = Graph([
            EdgeType("strong", "S", "S", accuracy=0.99),
            EdgeType("weak", "S", "S", accuracy=0.60),
        ])
        for x in "ABD":
            g.add_node(Node(x, "S", x))
        g.add_edge("A", "weak", "D")                      # direct but unreliable
        g.add_edge("A", "strong", "B")
        g.add_edge("B", "strong", "D")                    # two hops, reliable
        paths = g.transitive("A", "strong") + g.transitive("A", "weak")
        # Within one edge type there is one path each; the design point is that
        # transitive() keeps the best per target when alternatives exist:
        g2 = Graph([EdgeType("dep", "S", "S", accuracy=0.9)])
        for x in "ABCD":
            g2.add_node(Node(x, "S", x))
        g2.add_edge("A", "dep", "B")
        g2.add_edge("B", "dep", "D")                      # 2 hops: 0.81
        g2.add_edge("A", "dep", "D", confidence=0.95)     # 1 hop:  0.95
        best_d = next(p for p in g2.transitive("A", "dep") if p.edges[-1].target == "D")
        self.assertAlmostEqual(best_d.confidence, 0.95, places=4)
        self.assertEqual(best_d.hops, 1)


if __name__ == "__main__":
    unittest.main()
