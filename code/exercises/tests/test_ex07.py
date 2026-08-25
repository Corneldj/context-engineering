import unittest

from exercises._loader import load

ex = load("ex07_judge_rubric")

SOURCES = [
    {"id": "q2", "text": "Q2 revenue was 4200 thousand dollars, up 12 percent."},
    {"id": "hr", "text": "Headcount grew to 87 across 3 offices."},
]

# Expected scores, reasoned check by check (the exercise: reproduce them):
#   perfect            -> CITES+NO_FAKES+GROUNDED+HONEST            = 4
#   no citation        -> NO_FAKES (vacuous) + HONEST; numbers have
#                         no cited source to ground them            = 2
#   fabricated cite    -> CITES (q2 valid) + GROUNDED + HONEST;
#                         audit9 kills NO_FAKES                     = 3
#   ungrounded number  -> loses only GROUNDED (15 appears nowhere)  = 3
#   uncited source     -> 87 is real but its source is not cited    = 3
#   honest empty       -> everything except CITES                   = 3
#   hallucinated empty -> nothing survives an empty context         = 0
#   false absence      -> NO_FAKES + GROUNDED (no numbers) only     = 2
CASES = [
    ("perfect", "Revenue rose 12 percent to 4200 [S:q2].", SOURCES, 4),
    ("no citation at all", "Revenue rose 12 percent to 4200.", SOURCES, 2),
    ("fabricated citation", "Revenue rose 12 percent [S:q2] per audit [S:audit9].",
     SOURCES, 3),
    ("ungrounded number", "Revenue rose 15 percent [S:q2].", SOURCES, 3),
    ("number from an uncited source", "Headcount is 87 [S:q2].", SOURCES, 3),
    ("honest about an empty context",
     "That is not in the provided sources.", [], 3),
    ("hallucinating against an empty context",
     "Revenue rose 12 percent to 4200 [S:q2].", [], 0),
    ("false claim of absence", "That is not in the provided sources.", SOURCES, 2),
]


class TestRubric(unittest.TestCase):
    def test_each_case_scores_as_a_careful_human_would(self):
        for label, answer, sources, expected in CASES:
            with self.subTest(label):
                self.assertEqual(ex.score(answer, sources), expected)

    def test_scores_are_bounded(self):
        for _, answer, sources, _ in CASES:
            self.assertIn(ex.score(answer, sources), range(0, 5))


if __name__ == "__main__":
    unittest.main()
