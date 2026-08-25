import unittest

from ce import DEFAULT_FROZEN, MetaHarness, Scores
from exercises._loader import load

ex = load("ex10_heldout_gate")

BASE = Scores(0.70, 0.70, per_category={"invoices": 0.75, "contracts": 0.65})

QUARTET = {
    "genuine": Scores(0.78, 0.76,
                      per_category={"invoices": 0.82, "contracts": 0.71}),
    "overfit": Scores(0.87, 0.705,
                      per_category={"invoices": 0.90, "contracts": 0.66}),
    "reward_hack": Scores(0.76, 0.75,
                          per_category={"invoices": 0.88, "contracts": 0.40}),
    "noise": Scores(0.705, 0.705,
                    per_category={"invoices": 0.755, "contracts": 0.655}),
}


class TestGate(unittest.TestCase):
    def setUp(self):
        self.gate = ex.make_gate(200)

    def test_min_gain_means_several_flipped_cases_not_one(self):
        self.assertGreaterEqual(self.gate.min_gain, 3 / 200,
                                "0.5% on 200 cases is one lucky case")

    def test_only_the_genuine_candidate_survives(self):
        verdicts = {name: self.gate.judge(BASE, s).accepted
                    for name, s in QUARTET.items()}
        self.assertEqual(verdicts, {
            "genuine": True, "overfit": False,
            "reward_hack": False, "noise": False,
        })

    def test_the_reward_hack_is_named_for_what_it_is(self):
        v = self.gate.judge(BASE, QUARTET["reward_hack"])
        self.assertIn("contracts", v.reason,
                      "per-category tracking is what catches a hack the mean hides")


class TestEditableSurfaces(unittest.TestCase):
    def test_constructible_into_a_metaharness(self):
        # Raises FrozenSurfaceError if anything frozen slipped in.
        MetaHarness(editable=ex.editable_surfaces(),
                    evaluate=lambda h: Scores(0.5, 0.5))

    def test_the_useful_surfaces_are_present(self):
        surfaces = ex.editable_surfaces()
        self.assertIn("system_prompt", surfaces)
        self.assertIn("workflow", surfaces)

    def test_nothing_frozen_and_no_schema(self):
        surfaces = ex.editable_surfaces()
        self.assertFalse(surfaces & DEFAULT_FROZEN)
        self.assertFalse(any("schema" in s for s in surfaces),
                         "loosening the output schema is how total=0 'passes'")


if __name__ == "__main__":
    unittest.main()
