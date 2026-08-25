import unittest

from ce import OntologyError
from exercises._loader import load

ex = load("ex08_ontology")


class TestOntologyGate(unittest.TestCase):
    def setUp(self):
        self.g = ex.build_graph()

    def test_an_undeclared_edge_type_is_refused(self):
        node_ids = list(self.g.nodes)
        with self.assertRaises(OntologyError):
            self.g.add_edge(node_ids[0], "is_associated_with", node_ids[1])

    def test_the_edge_vocabulary_is_small(self):
        self.assertLessEqual(len(self.g.edge_types), 4,
                             "three edge types answer everything asked here")

    def test_who_owns_the_service_that_caused_inc7(self):
        incident = next(n.id for n in self.g.nodes.values() if "INC-7" in n.name)
        caused = self.g.out_edges(incident)
        self.assertEqual(len(caused), 1, "INC-7 should have exactly one cause")
        deploy = caused[0].target
        touched = {e.target for e in self.g.out_edges(deploy)}
        self.assertTrue(touched, "the deploy should have touched something")
        owners = {
            e.source for svc in touched for e in self.g.in_edges(svc, type="owns")
        }
        owner_names = {self.g.nodes[o].name for o in owners}
        self.assertEqual(owner_names, {"Payments"})

    def test_the_absence_query(self):
        service_type = next(
            n.type for n in self.g.nodes.values() if "legacy-cron" in n.name
        )
        own_type = next(t for t in self.g.edge_types if "own" in t.lower())
        orphans = self.g.missing(service_type, own_type, direction="in")
        self.assertEqual([self.g.nodes[n.id].name for n in orphans], ["legacy-cron"])


if __name__ == "__main__":
    unittest.main()
