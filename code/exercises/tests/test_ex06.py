import unittest

from ce import tokens as tok
from exercises._loader import load

ex = load("ex06_compaction_preserve")

GOAL = "Migrate the suite from unittest to pytest without breaking INC-7's fix."


def trajectory():
    msgs = [
        {"role": "system", "content": "You migrate test files."},
        {"role": "user", "content": GOAL},
    ]
    for i in range(8):
        msgs.append({"role": "assistant", "content": f"okay, looking at file {i} now..."})
        msgs.append({"role": "tool", "name": "read_file", "content": "x" * 800})
    msgs.append({"role": "assistant",
                 "content": "TRIED: bulk sed rewrite. FAILED: broke fixtures in test_7."})
    msgs.append({"role": "assistant", "content": "The regression traces to INC-42."})
    return msgs


def total(msgs):
    return sum(tok.count(str(m.get("content", ""))) for m in msgs)


class TestShrink(unittest.TestCase):
    def setUp(self):
        self.budget = 575   # forces chatter drops; protected content alone is ~543
        self.out = ex.shrink(trajectory(), self.budget)
        self.texts = [str(m.get("content", "")) for m in self.out]

    def test_fits_the_budget(self):
        self.assertLessEqual(total(self.out), self.budget)

    def test_the_goal_survives_verbatim(self):
        self.assertIn(GOAL, self.texts)

    def test_dead_ends_survive(self):
        self.assertTrue(any("TRIED: bulk sed rewrite" in t for t in self.texts),
                        "drop the dead end and the agent will retry it")

    def test_exact_identifiers_survive(self):
        joined = " ".join(self.texts)
        self.assertIn("INC-42", joined)
        self.assertIn("INC-7", joined)

    def test_stale_tool_results_were_cleared_not_dropped(self):
        stubs = [t for t in self.texts if "cleared" in t]
        self.assertTrue(stubs, "old tool results should become one-line stubs "
                               "(silent removal reads as 'this never happened')")

    def test_recent_tool_results_stay_verbatim(self):
        full = [m for m in self.out
                if m.get("role") == "tool" and "cleared" not in str(m.get("content"))]
        self.assertGreaterEqual(len(full), 1)

    def test_chatter_was_the_sacrifice(self):
        chatter = [t for t in self.texts if "looking at file" in t]
        self.assertLess(len(chatter), 8, "some chatter should have been dropped")


if __name__ == "__main__":
    unittest.main()
