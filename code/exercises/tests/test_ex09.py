import unittest

from ce import EdgeType, Graph, GraphNode
from exercises._loader import load

ex = load("ex09_bitemporal")

MAR, FEB20, MAR10 = 300, 250, 400


def fresh_graph() -> Graph:
    g = Graph([EdgeType("owns", "Team", "Service", time_varying=True)])
    g.add_node(GraphNode("team_a", "Team", "Team A"))
    g.add_node(GraphNode("team_b", "Team", "Team B"))
    g.add_node(GraphNode("svc", "Service", "payments-api"))
    g.add_edge("team_a", "owns", "svc", t_valid=0, t_created=0)
    return g


def owner_at(g, when, believed_at=None):
    owners = [
        e.source for e in g.edges
        if e.type == "owns" and e.true_at(when)
        and (believed_at is None or e.believed_at(believed_at))
    ]
    return sorted(set(owners))


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.g = fresh_graph()
        ex.record_transfer(self.g, "svc", "team_a", "team_b", at=MAR)

    def test_what_is_true_now(self):
        self.assertEqual(owner_at(self.g, 900), ["team_b"])

    def test_what_was_true_before_the_transfer(self):
        self.assertEqual(owner_at(self.g, 100), ["team_a"])

    def test_nothing_was_deleted(self):
        self.assertEqual(len([e for e in self.g.edges if e.type == "owns"]), 2)


class TestCorrection(unittest.TestCase):
    def setUp(self):
        self.g = fresh_graph()
        ex.record_transfer(self.g, "svc", "team_a", "team_b", at=MAR)
        ex.correct_transfer(self.g, "svc", "team_a", "team_b",
                            actual_at=FEB20, discovered_at=MAR10)

    def test_corrected_truth_at_the_disputed_moment(self):
        """At t=280 — after the REAL transfer, before the recorded one —
        the corrected record must say Team B owned it."""
        current_belief = [
            e.source for e in self.g.edges
            if e.type == "owns" and e.true_at(280) and e.believed_at(900)
        ]
        self.assertEqual(sorted(set(current_belief)), ["team_b"])

    def test_what_we_believed_before_the_correction_is_still_answerable(self):
        """On day 350 — before we discovered the error — we believed Team A
        owned it at t=280. That belief must remain queryable."""
        old_belief = [
            e.source for e in self.g.edges
            if e.type == "owns" and e.true_at(280) and e.believed_at(350)
        ]
        self.assertEqual(sorted(set(old_belief)), ["team_a"])

    def test_still_nothing_deleted(self):
        self.assertGreaterEqual(len([e for e in self.g.edges if e.type == "owns"]), 4)


if __name__ == "__main__":
    unittest.main()
