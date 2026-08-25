"""Tests for continuous vector memory graphs (Module 9, Lesson 3).

The claims under test: entry+expand answers what pure vector cannot; vectors
outlive truth but validity filters them; the graph is continuous (embed cost
per write is O(neighbourhood), not O(corpus)); node embeddings refresh at the
mutation point.
"""

import unittest

from ce.graph import EdgeType, Graph, Node, OntologyError
from ce.vectorgraph import VectorMemoryGraph, cosine, hash_embed


def build() -> VectorMemoryGraph:
    g = Graph([
        EdgeType("subscribes_to", "Customer", "Plan", time_varying=True, accuracy=0.95),
        EdgeType("billed_to", "Invoice", "Customer", accuracy=0.98),
        EdgeType("mentions", "Ticket", "Plan", accuracy=0.90),
    ])
    vmg = VectorMemoryGraph(g)
    vmg.add_node(Node("kim", "Customer", "Kim Nakamura"))
    vmg.add_node(Node("starter", "Plan", "Starter"))
    vmg.add_node(Node("growth", "Plan", "Growth"))
    vmg.add_node(Node("inv7712", "Invoice", "Invoice 7712"))
    return vmg


class TestEmbedder(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(hash_embed("kim pays monthly"), hash_embed("kim pays monthly"))

    def test_overlap_scores_higher_than_disjoint(self):
        a = hash_embed("invoice for kim nakamura")
        self.assertGreater(cosine(a, hash_embed("kim nakamura invoice history")),
                           cosine(a, hash_embed("orbital mechanics primer")))

    def test_empty_text_is_a_zero_vector_not_a_crash(self):
        self.assertEqual(cosine(hash_embed(""), hash_embed("anything")), 0.0)


class TestOntologyStillGates(unittest.TestCase):
    def test_the_wrapped_graph_quality_gate_is_not_bypassed(self):
        vmg = build()
        with self.assertRaises(OntologyError):
            vmg.add_fact("kim", "is_associated_with", "growth")


class TestEntryExpandBeatsPureVector(unittest.TestCase):
    """The core claim: a fact sharing NO vocabulary with the query is
    unreachable by pure vector search, and reachable via entry + expansion."""

    def setUp(self):
        self.vmg = build()
        self.vmg.add_fact("inv7712", "billed_to", "kim",
                          text="Invoice 7712 billed to Kim Nakamura")
        self.vmg.add_fact("kim", "subscribes_to", "growth",
                          text="Kim Nakamura signed up for Growth")
        # Query shares tokens with the invoice fact only — deliberately no
        # overlap with the answer fact, not even stopwords ("for", "up").
        self.query = "which tier is invoice 7712 under"

    def test_pure_vector_misses_the_connected_answer(self):
        texts = [r.text for r in self.vmg.semantic_only(self.query)]
        self.assertNotIn("Kim Nakamura signed up for Growth", texts)

    def test_recall_reaches_it_through_the_graph(self):
        results = self.vmg.recall(self.query, hops=2)
        texts = [r.text for r in results]
        self.assertIn("Kim Nakamura signed up for Growth", texts)
        answer = next(r for r in results if "Growth" in r.text)
        self.assertEqual(answer.hops, 2)
        self.assertIn("hop 2", answer.explain())


class TestVectorsOutliveTruth(unittest.TestCase):
    """Keep the embedding, filter by validity — deleting breaks as-of,
    not filtering pollutes now."""

    def setUp(self):
        self.vmg = build()
        starter = self.vmg.add_fact("kim", "subscribes_to", "starter",
                                    text="Kim Nakamura signed up for Starter",
                                    t_valid=0, t_created=0)
        self.vmg.supersede(starter, new_target="growth", at=300,
                           text="Kim Nakamura signed up for Growth")

    def test_now_queries_see_only_the_current_fact(self):
        texts = [r.text for r in self.vmg.recall("Kim Nakamura signed up")]
        self.assertIn("Kim Nakamura signed up for Growth", texts)
        self.assertNotIn("Kim Nakamura signed up for Starter", texts)

    def test_as_of_queries_still_find_the_superseded_fact(self):
        texts = [r.text for r in self.vmg.recall("Kim Nakamura signed up", at=200)]
        self.assertIn("Kim Nakamura signed up for Starter", texts)
        self.assertNotIn("Kim Nakamura signed up for Growth", texts)

    def test_even_pure_vector_memory_needs_the_validity_filter(self):
        now_texts = [r.text for r in self.vmg.semantic_only("Starter signed up")]
        self.assertNotIn("Kim Nakamura signed up for Starter", now_texts)
        then_texts = [r.text for r in self.vmg.semantic_only("Starter signed up", at=200)]
        self.assertIn("Kim Nakamura signed up for Starter", then_texts)


class TestContinuity(unittest.TestCase):
    def test_write_cost_is_independent_of_corpus_size(self):
        """Embed-on-write is O(neighbourhood). A batch rebuild is O(corpus)."""
        vmg = build()
        for i in range(30):
            vmg.add_node(Node(f"t{i}", "Ticket", f"Ticket {i}"))
            vmg.add_fact(f"t{i}", "mentions", "starter", text=f"ticket {i} asks about starter")
        before = vmg.embed_calls
        vmg.add_node(Node("t_new", "Ticket", "Ticket new"))
        vmg.add_fact("t_new", "mentions", "growth", text="new ticket asks about growth")
        delta = vmg.embed_calls - before
        # 1 node add + (1 fact + 2 endpoint refreshes) = 4. Never ~66.
        self.assertLessEqual(delta, 4)

    def test_node_embeddings_refresh_at_the_mutation_point(self):
        vmg = build()
        starter = vmg.add_fact("kim", "subscribes_to", "starter",
                               text="Kim Nakamura signed up for Starter")
        before_entries = dict(vmg.entry_points("Growth", k=4))
        vmg.supersede(starter, new_target="growth",
                      at=300, text="Kim Nakamura signed up for Growth")
        after_entries = dict(vmg.entry_points("Growth", k=4))
        # After the supersede, Kim's summary contains the Growth fact, so a
        # Growth query now enters through Kim — stale summaries would not.
        self.assertGreater(after_entries.get("kim", 0.0), before_entries.get("kim", 0.0))

    def test_the_departed_endpoint_is_refreshed_too(self):
        """Kim's summary must also STOP claiming Starter."""
        vmg = build()
        starter = vmg.add_fact("kim", "subscribes_to", "starter",
                               text="Kim Nakamura signed up for Starter")
        vmg.supersede(starter, new_target="growth",
                      at=300, text="Kim Nakamura signed up for Growth")
        summary = vmg._node_summary("kim")
        self.assertNotIn("Starter", summary)
        self.assertIn("Growth", summary)


class TestStats(unittest.TestCase):
    def test_stats_report_the_cost_meter(self):
        vmg = build()
        s = vmg.stats()
        self.assertEqual(s["nodes"], 4)
        self.assertEqual(s["facts"], 0)
        self.assertGreater(s["embed_calls"], 0)


if __name__ == "__main__":
    unittest.main()
